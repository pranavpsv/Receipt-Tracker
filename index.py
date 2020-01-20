import boto3
from PIL import Image
from flask import Flask, render_template, url_for, request, redirect
import pytesseract
from flask_mysqldb import MySQL
from fuzzywuzzy import fuzz
import mysqlinfo
import os
import cv2
import numpy as np
import re
import awscredentials

app = Flask(__name__)
app.config["MYSQL_USER"] = mysqlinfo.login["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = mysqlinfo.login["MYSQL_PASSWORD"]
app.config["MYSQL_HOST"] = mysqlinfo.login["MYSQL_HOST"]
app.config["MYSQL_DB"] = mysqlinfo.login["MYSQL_DB"]
app.config["MYSQL_CURSORCLASS"] = mysqlinfo.login["MYSQL_CURSORCLASS"]
mysql = MySQL(app)




vendors_list = ["Walmart", "Coop", "Zehr's", "Best Buy", "Amazon", "Spencer", "Sobey's", "Migros"]
vendor_categories = {"Walmart": "Grocery", "Zehr's" : "Grocery" , "Coop" : "Grocery", "Sobey's" : "Grocery", 
"Best Buy": "Electronics", "Amazon": "Online Retailer", "Migros": "Grocery", "Nike": "Sports", 
"Adidas": "Sports", "SportsChek" : "Sports", "Spencer": "Grocery"}

@app.route("/login", methods = ["GET", "POST"])
def login():
    cur = mysql.connection.cursor()
    global loggedIn
    loggedIn = False
    if request.method == "GET":
        return render_template("login.html")
    else:
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            return redirect("/start")



@app.route("/start", methods=["GET", "POST"])
def home():
    return render_template("home.html")

def performOCR(documentName):
    global receiptList
    receiptList = []
    with open(documentName, 'rb') as document:
        imageBytes = bytearray(document.read())
    textract = boto3.client('textract', aws_access_key_id= awscredentials.aws["access_id"],
    aws_secret_access_key=awscredentials.aws["access_key"],
    region_name='us-west-2')

    response = textract.detect_document_text(Document={'Bytes': imageBytes})
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            print(item["Text"])
            receiptList.append(item["Text"])



@app.route("/upload", methods=["GET", "POST"])
def processImage():
    global fuzzy_match_threshold
    fuzzy_match_threshold = 70
    if request.files:    
        image = request.files['image']
        print(image)
        app.config["IMAGE_UPLOADS"] = "./static"
        image.save(os.path.join(app.config["IMAGE_UPLOADS"], image.filename))
        performOCR(os.path.join(app.config["IMAGE_UPLOADS"], image.filename))
        VendorParser()
        TotalParser()
    return render_template("results.html", merchant=merchant, total=total, category=category )

@app.route("/update", methods=["POST"])


def ItemsPriceParser():
    global items
    items = {}
    for index, word in enumerate(receiptList):
        if re.search(r"^[a-zA-Z]", word) is not None:
            items[word] = 0
            currIdx = index + 1
            priceLst = []
            try:
                while re.search(r"^[a-zA-Z]", receiptList[currIdx]) is None:
                    if (re.findall(r"[0-9]*[.,][0-9][0-9]",receiptList[currIdx])) != []:
                        items[word] = float(re.findall(r"[0-9]*[.,][0-9][0-9]",item)[0])
                        break
                    else:
                        currIdx += 1
            except:
                continue
    print(items)
            


def DateParser():
    pass

def LocationParser():
    pass


def VendorParser():
    global merchant
    global category
    merchant = "Unknown",
    category = "Unknown"
    for vendor in vendor_categories.keys():
        for word in receiptList:
            if fuzz.token_set_ratio(word, vendor) > fuzzy_match_threshold:
                merchant = vendor
                category = vendor_categories[merchant]


def TotalParser():
    global total 
    for index, word in enumerate(receiptList):
        if fuzz.token_set_ratio(word, "total") > fuzzy_match_threshold:
            try:
                total = float(receiptList[index + 1])
            except:
                continue

if __name__ == "__main__":
    app.run(debug=True)

