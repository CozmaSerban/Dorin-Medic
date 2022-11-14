from genericpath import exists
from bson import json_util
from operator import le, methodcaller
from flask import Flask, request, redirect, url_for, render_template, session
import pymongo, json
from datetime import datetime, timedelta
from dateutil.relativedelta import *
from auth import auth
from bson.json_util import dumps
import logging
import xlsxwriter

client = pymongo.MongoClient("mongodb+srv://serban:serban@cluster0.oi6hu.mongodb.net/?retryWrites=true&w=majority")
db = client.get_database('medic')
records = db.patients
tb_analize = db.analize

medicatii = {
    "interferon_beta":[
        {"analiza":"AST, ALT", "perioada":[{"luna": 0, "count":1},{"luna": 1, "count":1},{"luna": 3, "count":1},{"luna": 6, "count":99}]},
        {"analiza":"HLG", "perioada":[{"luna": 0, "count":1},{"luna": 1, "count":1},{"luna": 3, "count":1},{"luna": 6, "count":99}]},
        {"analiza":"Hormoni tiroidieni (TSH, fT3, fT4)", "perioada":[{"luna": 0, "count":1},{"luna": 6, "count":99}]},
        {"analiza":"RMN", "perioada":[{"luna": 0, "count":1},{"luna": 12, "count":99}]},
    ],
    "glatiramer_acetat":[
        {"analiza":"AST, ALT", "perioada":[{"luna": 0, "count":1},{"luna": 12, "count":99}]},
        {"analiza":"HLG", "perioada":[{"luna": 0, "count":1},{"luna": 12, "count":99}]},
        {"analiza":"Hormoni tiroidieni (TSH, fT3, fT4)", "perioada":[{"luna": 0, "count":1},{"luna": 12, "count":99}]},
        {"analiza":"RMN", "perioada":[{"luna": 0, "count":1},{"luna": 12, "count":99}]},
    ],

}

app = Flask(__name__)
app.secret_key = "super secret key"
# app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=2)
app.register_blueprint(auth)


@app.route("/")
def index():
    if "email" in session:
        return render_template("index.html")
    else:
        return redirect(url_for("auth.login"))

@app.route("/patients")
def patients():
    if "email" in session:
        return render_template("patients.html")
    else:
        return redirect(url_for("auth.login"))

@app.route("/add_patient", methods=["POST"])
def add_patient():
    data = request.get_json(force=True)
    
    #needs check for duplicates
    data["medic"] = session["email"]
    if is_unique(records,"cnp",data['cnp']):
        for key in medicatii:
            if key[:3] == data["tratament"].lower()[:3]:
                    data["analize"] = medicatii[key]
        for analiza in data["analize"]:
            for entry in analiza["perioada"]:
                now = datetime.now()
                new = now + relativedelta(months=entry["luna"])
                entry["time"] = str(new.month)+"/"+str(new.year)

        records.insert_one(data)
        print("Your data{}".format(data))
        add_analize(data=data)
    else:
        print("Patient {} already exists".format(data['cnp']))
    
    return "asdasd"

@app.route("/update_patient", methods=["POST"])
def update_patient():
    data = request.get_json(force=True)
    print(data)
    #needs check for duplicates
    myquery = { "cnp": data["cnp"] }
    newvalues = { "$set": { "nume": data["nume"] ,"cnp":data["cnp"], "prenume": data["prenume"], "extranotite": data["extranotite"]} }
    records.update_one(myquery, newvalues)    
    return "asdasd"

@app.route("/get_patient", methods=["GET"])
def get_patient():
    print(list(records.find({},{ "medic": session["email"] })))
    
    data = dumps(list(records.find({ "medic": session["email"] })))
    return data

@app.route("/get_record", methods=["GET"])
def get_record():

    update_records()
    print(list(tb_analize.find({},{ "medic": session["email"] })))
    now = datetime.now()
    print(str(now.month)+"/"+str(now.year))
    
    data = dumps(list(tb_analize.find({ "medic": session["email"] })))
    return data

def update_records():
    print("Updating records..")
    now = datetime.now()
    timp = str(now.month)+"/"+str(now.year)
    tb_analize.delete_many({ "medic": session["email"] })
    patients = list(records.find({ "medic": session["email"] }))
    for patient in patients:
        for analiza in patient["analize"]:
            for period in analiza["perioada"]:
                if period["count"] != 0:
                    if timp == period["time"]:
                        record = {}
                        record["medic"] = patient["medic"]
                        record["cnp"] = patient["cnp"]
                        record["nume"] = patient["nume"]
                        record["prenume"] = patient["prenume"]
                        record["analiza"] = analiza["analiza"]
                        record["tratament"] = patient["tratament"]
                        record["time"] = period["time"]
                        print("To be inserted {}".format(record))
                        tb_analize.insert_one(record)
    
@app.route("/generate_xls", methods=["GET"])
def generate_xls():
    workbook = xlsxwriter.Workbook('patients.xlsx')
    worksheet = workbook.add_worksheet()
    row = 0
    col = 0
    print("PULA")
    return "alskdmas"



@app.route("/delete_patient", methods=["POST"])
def delete_patient():
    print("Delete is executed")
    data = request.get_json(force=True)
    records.delete_one({"cnp":data['cnp']})
    tb_analize.delete_many({"cnp":data['cnp']})
    #fix refresh page
    return render_template("patients.html")

@app.route("/checked_analiza", methods=["POST"])
def check_analiza():
    print("Delete is executed")
    now = datetime.now()
    acum = str(now.month)+"/"+str(now.year)
    data = request.get_json(force=True)
    tb_analize.delete_one({"cnp":data['cnp'], "analiza":data["analiza"]})
    patient = list(records.find({"cnp":data['cnp']}))[0]
    records.delete_one({"cnp":data['cnp']})
    analize = patient["analize"]
    for analiza in analize:
        if analiza["analiza"] == data["analiza"]:
            for timp in analiza["perioada"]:
                if timp["time"] == acum and timp["count"] !=0:
                    update_date = datetime.now()
                    updated = update_date + relativedelta(months=timp["luna"]) #se face update la timp in baza de date si se face -- la counter
                    timp["time"]= str(updated.month)+"/"+str(updated.year)
                    timp["count"] = timp["count"] - 1
           
    records.insert_one(patient)
                    

    #fix refresh page
    return render_template("patients.html")

@app.route("/details_patient", methods=["GET"])
def details_patient():
    print("Details is executed")
    args = request.args
   
    data = records.find({"cnp": args["cnp"]})
    data = list(data)
    info = "Nu sunt date!"
    try:
        info = data[0]["extranotite"]
    except:
        print("NU SUNT INFO")
        
    
    #fix refresh page
    return {"notes": info}

@app.route("/change_patient", methods=["GET"])
def change_patient():
    print("CHANGE DETAUKS is exeai cuted")
    args = request.args
   
    data = records.find({"cnp": args["cnp"]})
    data = list(data)
    print(data[0])

    #fix refresh page
    return json.dumps(data[0], indent=4, default=json_util.default)



#used to add data to analize table from add_patient form 
def add_analize(data):
    
    analize = data["analize"]
    now = datetime.now()
    print(now)
    datum = str(now.month)+"/"+str(now.year)
    for analiza in analize:
        for period in analiza["perioada"]:
            if period["count"] != 0:
                if datum == period["time"]:
                    print(period)
                    print(datum)
                    print(period["time"])
                    record = {}
                    record["medic"] = data["medic"]
                    record["cnp"] = data["cnp"]
                    record["nume"] = data["nume"]
                    record["prenume"] = data["prenume"]
                    record["analiza"] = analiza["analiza"]
                    record["tratament"] = data["tratament"]
                    record["time"] = period["time"]
                    print("To be inserted {}".format(record))
                    tb_analize.insert_one(record)
 

    
   

def is_unique(collection,field, value):
    
    #result = collection.count_documents({"\""+field+"\"": value})
    result = collection.count_documents({field: value})
    if result == 0:
        return True
    else:
        return False

