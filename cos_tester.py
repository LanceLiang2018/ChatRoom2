from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

secret_id = 'AKIDcq7HVrj0nlAWUYvPoslyMKKI2GNJ478z'
secret_key = '70xZrtGAwmf6WdXGhcch3gRt7hV4SJGx'
region = 'ap-chengdu'
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
# 2. 获取客户端对象
client = CosS3Client(config)

bucket = 'chatroom-1254016670'

file_name = 'test.md'
with open('test.md', 'rb') as fp:
    response = client.put_object(
        Bucket=bucket,
        Body=fp.read(),
        Key=file_name,
        StorageClass='STANDARD',
        EnableMD5=False
    )
print(response['ETag'])
