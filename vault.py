import json
import boto3
import base64
from botocore.exceptions import ClientError

 
# Get the name of vaults. 
def get_secrets():
    session = boto3.session.Session()
    client = session.client('secretsmanager')
    try:
        response = client.list_secrets()
        return response
    except ClientError as e:
        raise Exception("boto3 client error in get_all_secrets: " + e.__str__())
    except Exception as e:
        raise Exception("Unexpected error in get_all_secrets: " + e.__str__())


def lambda_handler(event, context):

    region_name = "us-east-1"
    response = ""
    responseList=[]
    seckey = event["queryStringParameters"]['Name']
    get_secret_value_response=''

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    vaults = get_secrets()

    for vault in vaults['SecretList']:
        secret_name = vault['Name']
        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for
                raise e
        else:
            # Decrypts secret using the associated KMS.
            # Depending on whether the secret is a string or binary, response will be populated.
            if 'SecretString' in get_secret_value_response:
                secrets = get_secret_value_response['SecretString']
                secobj = json.loads(secrets)
                if seckey in secobj:
                    describe_secret = client.describe_secret(SecretId=secret_name)
                    if 'CreatedDate' in describe_secret:
                        crdate = describe_secret['CreatedDate']
                    response =  { "Vault": secret_name,"Key":seckey,"Value": secobj[seckey], 'CreatedDate':str(crdate)}
            else:
                response = base64.b64decode(get_secret_value_response['SecretBinary'])
        responseList.append(response)
    # if response if null, implying key not found.
    if ( response == "" ):
        responseList.clear()
        responseList.append("Invalid Key")

    return {
        'statusCode': 200,
        'body': json.dumps(responseList)
    }
