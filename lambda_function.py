import json
import os
import re
import boto3
from boto3.dynamodb.conditions import Key

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

ddb = boto3.resource("dynamodb", region_name='us-east-1')
table = ddb.Table("washer")
table2 = ddb.Table("washer_broadcast")


def lambda_handler(event, context):
    line_bot_api = LineBotApi(os.environ['YOUR_CHANNEL_ACCESS_TOKEN'])
    handler = WebhookHandler(os.environ['YOUR_CHANNEL_SECRET'])
    
    #query from dynamo DB
    response = table.query(KeyConditionExpression=Key('id').eq('washer01'),ScanIndexForward=False) # true = ascending, false = descending)
    broaded = table2.query(KeyConditionExpression=Key('id').eq('washer01'),ScanIndexForward=False)
    
    #text status
    status = response['Items'][0]['washer_data']['state'] + " \nTime left  " +  str(response['Items'][0]['washer_data']['minute']) + ":" + str(response['Items'][0]['washer_data']['seconds'])
    isbroaded = broaded['Items'][0]['broadcastAlready']
    print(response)
    print(isbroaded)
    
    annoucemsg = "#01 is already done!\nเครื่องหมายเลข 1 ซักเสร็จแล้ว"
    
    #check if status is DONE WASHING broast to user
    if (str(response['Items'][0]['washer_data']['state']) == "DONE WASHING") and not isbroaded:
        line_bot_api.broadcast(TextSendMessage(text=annoucemsg))
        
        #update new boolean to broadcast only once
        res = table2.update_item(
                Key={'id':'washer01'},
                UpdateExpression="SET broadcastAlready=:bc",
                ExpressionAttributeValues={':bc': True},
                ReturnValues="UPDATED_NEW"
                )
        print(res)
    
    #check if status is others will change boolean status to False
    if (str(response['Items'][0]['washer_data']['state']) == "IDLE") and isbroaded:
        #update new boolean to False
        res = table2.update_item(
                Key={'id':'washer01'},
                UpdateExpression="SET broadcastAlready=:bc",
                ExpressionAttributeValues={':bc': False},
                ReturnValues="UPDATED_NEW"
                )
        print(res)
    
    #reply to user function
    def replying():
        x1 = re.search("Status|status|STATUS|สถานะ", msg['events'][0]['message']['text'])
    
        warnmsg = "Invalid input\nPlease send \"Status\" or \"status\" or \"STATUS\" or \"สถานะ\""
        warnmsg2 = "คำสั่งไม่ถูกต้อง กรุณาป้อนคำสั่งใหม่ ดังนี้\n Status หรือ status หรือ STATUS หรือ สถานะ"
    
        if x1:
            line_bot_api.reply_message(
                msg['events'][0]['replyToken'],
                TextSendMessage(text=status)
            )
        else:
            line_bot_api.reply_message(
                msg['events'][0]['replyToken'],
                TextSendMessage(text=warnmsg)
            )
            
            line_bot_api.push_message(msg['events'][0]['replyToken'], TextSendMessage(text=warnmsg2))
      
    #check is user send a request
    msg = json.loads(event["body"])
    if msg['events'][0]['replyToken'] != None:
        replying()
    
    return {
        "statusCode": 200,
        "body": json.dumps({"message": 'ok'})
    }