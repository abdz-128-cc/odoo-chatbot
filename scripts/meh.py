# import os
# from pymilvus import connections, utility
# from dotenv import load_dotenv
#
# load_dotenv()
#
# # Use the same connection settings your app uses:contentReference[oaicite:7]{index=7}】:contentReference[oaicite:9]{index=9}】
# use_zilliz = True
# alias = "default"
# name = "employee_handbook_data"  # collection to drop
#
# if use_zilliz:
#     zid = os.getenv("ZILLIZ_ID"); region = os.getenv("ZILLIZ_REGION"); token = os.getenv("ZILLIZ_TOKEN")
#     assert all([zid, region, token]), "Missing ZILLIZ_ID/ZILLIZ_REGION/ZILLIZ_TOKEN env vars"
#     uri = f"https://{zid}.api.{region}.zillizcloud.com"
#     connections.connect(alias=alias, uri=uri, token=token, secure=True)
# else:
#     connections.connect(alias=alias, host="127.0.0.1", port="19530")
#
# if utility.has_collection(name):
#     utility.drop_collection(name)
#     print(f"Dropped collection: {name}")
# else:
#     print(f"Collection not found: {name}")


# one-off helper (run in a python shell from the same venv)
from pymilvus import connections, utility
import os
from dotenv import load_dotenv

load_dotenv()

zid, region, token = os.getenv("ZILLIZ_ID"), os.getenv("ZILLIZ_REGION"), os.getenv("ZILLIZ_TOKEN")
uri = f"https://{zid}.api.{region}.zillizcloud.com"
connections.connect(alias="default", uri=uri, token=token, secure=True)

name = "employee_handbook_data"
if utility.has_collection(name):
    utility.drop_collection(name)
    print("Dropped:", name)
