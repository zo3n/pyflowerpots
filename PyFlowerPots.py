import tkinter as tk
import sqlite3
import random
import hashlib
import time
import datetime
import PyWeather
import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tkinter import *
from tkinter import filedialog
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PyFlowerPots:
    def __init__(self, root):
        self.root = root
        self.curPage = "login"
        self.curUser = ""
        self.curStep = 0
        self.numPots = 0
        self.refreshTime = 15 # num of seconds by which the sensor data refreshes to newest one on home page
        self.lastTime = time.time()
        self.initData = True
        self.historyNew = False
        self.currentlyEditing = False
        self.logs = {}
        self.logElements = {}
        self.sensorData = {}
        self.favorites = {}
        self.favElements = {}
        self.db = sqlite3.connect("pots.db")
        
        # Defaults
        self.userData = {
            "adminUser" : "admin",
            "adminPw" : "admin",
            "adminName" : "Zvonimir",
            "adminSurname" : "Hadžić"
        }

        # Load new data if it exists
        if os.path.isfile("userdata.json"):
            with open("userdata.json", "r") as file_reader:
                self.userData = json.load(file_reader)
                print("Loaded pre-existing user data")
        else:
            print("Loaded default user data")

        self.adminUser = self.userData["adminUser"]
        self.adminPw = self.userData["adminPw"]
        self.adminName = self.userData["adminName"]
        self.adminSurname = self.userData["adminSurname"]
        self.cursor = self.db.cursor()
        self.db.execute("CREATE TABLE IF NOT EXISTS user_pots (id TEXT, name TEXT, desc TEXT, favorite TEXT, flower TEXT, state TEXT)")
        self.db.commit()
        self.weather = PyWeather.PyWeather()
        self.root.after(15000, self.createLog)
        self.root.after(15000, self.refreshHomeData)
        self.createWindow()


    def createWindow(self):
        self.width = 304
        self.height = 600
        self.graphWidth = 1024
        self.graphHeight = 300
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.title("PyFlowerPots")
        self.root.configure(bg = "white")
        self.createLoginGUI()

    def createLog(self):

        for id, value in self.sensorData.items():

            if value["humidity"] < 50:

                # Needs watering
                row = self.cursor.execute(f"SELECT * FROM user_pots WHERE id='{id}'")
                data = row.fetchone()
                potName = data[1]
                flower = data[4]

                # Don't do things for empty pots
                if flower != "no":
                    curTime = datetime.datetime.now().strftime("%H:%M:%S")
                    self.logs[curTime + str(random.randint(1, 999999))] = f"[{curTime}] Low humidity noticed on pot {potName}. Watering now..."
                    print(f"Low humidity noticed on pot {potName}. Watering now...")

                    if self.curPage == "history":
                        self.hideHistoryGui()
                        self.showHistoryGui()
                    else:
                        if not self.historyNew:
                            self.historyNew = True
                            try:
                                if self.imgHistNewLbl:
                                    self.imgHistNewLbl.place(x = 218)
                            except:
                                self.imgHistNew_ = Image.open("gui/notification.png")
                                self.imgHistNew = ImageTk.PhotoImage(self.imgHistNew_)
                                self.imgHistNewLbl = tk.Label(self.root, bg = "white", image = self.imgHistNew)
                                self.imgHistNewLbl.place(x = 218, y = self.height - self.navHeight + 2, width = 12, height = 12)

        self.root.after(15000, self.createLog)

    def getUsername(self):
        return self.inputUsrText.get()

    def getPwd(self):
        return self.inputPwdText.get()

    def getAddName(self):
        return self.addPotNameTxt.get()

    def getAddDesc(self):
        return self.addPotDescTxt.get()

    def createLoginGUI(self):
        # Title
        self.lblTitle = tk.Label(self.root, bg = self.root['bg'], font = ('Arial', 16), text = "PyFlowerPots")
        self.lblTitle.place(x = self.width * 0.250, y = 30)
        
        # Login Title
        self.lblLogin = tk.Label(self.root, bg = self.root['bg'], font = ('Arial', 20), text = "Login")
        self.lblLogin.place(x = self.width * 0.350, y = 150)

        # Username
        self.inputUsrText = tk.StringVar()
        self.inputUsr = tk.Entry(self.root, textvariable = self.inputUsrText, bg = self.root['bg'])
        self.inputUsr.place(x = self.width * 0.250, y = 250, height = 30, width = self.width * 0.5)
        self.inputUsrLabel = tk.Label(self.root, bg = self.root['bg'], text = "Username", font = ('Arial', 10))
        self.inputUsrLabel.place(x = self.width * 0.250, y = 225)

        # Password
        self.inputPwdText = tk.StringVar()
        self.inputPwd = tk.Entry(self.root, textvariable = self.inputPwdText, bg = self.root['bg'], show = "•")
        self.inputPwd.place(x = self.width * 0.250, y = 320, height = 30, width = self.width * 0.5)
        self.inputPwdLabel = tk.Label(self.root, bg = self.root['bg'], text = "Password", font = ('Arial', 10))
        self.inputPwdLabel.place(x = self.width * 0.250, y = 295)

        # Login Button
        self.btnPrijava = tk.Button(self.root, bg = self.root['bg'], text = "LOGIN", command = self.handleLogin)
        self.btnPrijava.place(x = self.width * 0.250, y = 380, width = self.width * 0.5, height = 30)

        # dev purposes to skip login until we finish screen after login one
        #self.curUser = "admin"
        #self.hideLoginGUI()
        #self.showBiljkeGUI()
        #print("Skipped login screen because of development mode")

    def hideLoginGUI(self):

        self.lblLogin.pack()
        self.lblLogin.pack_forget()

        self.inputUsr.pack()
        self.inputUsr.pack_forget()

        self.inputUsrLabel.pack()
        self.inputUsrLabel.pack_forget()

        self.inputPwd.pack()
        self.inputPwd.pack_forget()

        self.inputPwdLabel.pack()
        self.inputPwdLabel.pack_forget()

        self.btnPrijava.pack()
        self.btnPrijava.pack_forget()


    def handleLogin(self):
        if self.getUsername() == self.adminUser:
            if self.getPwd() == self.adminPw:
                self.curUser = self.getUsername()
                self.hideLoginGUI()
                self.showBiljkeGUI()
                print("Login successful")
            else:
                print("Incorrect password")
        else:
            print(f"Unknown user {self.getUsername()}")

    def hideCurPage(self):
        if self.curPage == "home":
            self.hideHomeGui()
        elif self.curPage == "favorites":
            self.hideFavoriteGui()
        elif self.curPage == "add":
            self.hideAddGui()
        elif self.curPage == "history":
            self.hideHistoryGui()
        elif self.curPage == "settings":
            self.hideSettingsGui()

    def showPage(self, page):
        self.hideCurPage()
        if page == "home":
            self.c2.place(x = 0)
            self.lblCategory["text"] = "Your pots"
            self.showHomeGui()
        elif page == "favorites":
            self.c2.place(x = 60)
            self.lblCategory["text"] = "Your favorites"
            self.showFavoriteGui()
        elif page == "add":
            self.c2.place(x = 120)
            self.lblCategory["text"] = "Add pot"
            self.showAddGui()
        elif page == "history":

            self.c2.place(x = 180)
            self.lblCategory["text"] = "History"

            # Hide notification icon if there is active one on history page
            self.historyNew = False
            try:
                if self.imgHistNewLbl:
                    self.imgHistNewLbl.place(x = -500)
            except:
                pass

            self.showHistoryGui()

        elif page == "settings":
            self.c2.place(x = 240)
            self.lblCategory["text"] = "Settings"
            self.showSettingsGui()
        self.curPage = page

    def limitNameEntry(self, *args):
        value = self.addPotNameTxt.get()
        if len(value) > 16:
            self.addPotNameTxt.set(value[:16])

    def toggleFavorite(self, id, favorite, flower):
        
        # Empty pots cannot go in favorites
        if flower == "no":
            return

        newFavorite = favorite == "no" and "yes" or "no"
        self.db.execute(f"UPDATE user_pots SET favorite='{newFavorite}' WHERE id='{id}'")
        self.db.commit()
        self.favorites[id] = newFavorite == "yes" and True or False
        self.updateHomeGui()


    def deletePot(self, id):
        self.db.execute(f"DELETE FROM user_pots WHERE id='{id}'")
        self.db.commit()
        self.numPots -= 1
        self.curStep = 0
        print(f"Deleted pot {id} from database")
        self.updateHomeGui()

    def addUploadImage(self, id):
        self.filename = filedialog.askopenfilename(initialdir = "/", title = "Choose flower image")
        if len(self.filename) > 0:
            self.db.execute(f"UPDATE user_pots SET flower='{self.filename}' WHERE id='{id}'")
            self.db.commit()
            self.updateHomeGui()

    def openGraph(self, flower):

        # Don't display graph for empty pots
        if flower == "no":
            return

        self.graphRoot = tk.Toplevel(self.root, bg = self.root['bg'])
        self.graphRoot.title("PyFlowerPots - Graphs and details")
        self.graphRoot.geometry(f"{self.graphWidth}x{self.graphHeight}")
        
        self.tempData1 = {
            "id" : [],
            "humidity" : [],
        }

        self.tempData2 = {
            "id" : [],
            "ph" : [],
        }

        self.tempData3 = {
            "id" : [],
            "light" : [],
        }
        for id, data in self.sensorData.items():
            for column, value in data.items():
                if column == "humidity":
                    self.tempData1["id"].append(id[0:3])
                    self.tempData1["humidity"].append(value)
                elif column == "ph":
                    self.tempData2["id"].append(id[0:3])
                    self.tempData2["ph"].append(value)
                elif column == "light":
                    self.tempData3["id"].append(id[0:3])
                    self.tempData3["light"].append(value)

        self.df0 = pd.DataFrame(self.sensorData.items())

        self.df1 = pd.DataFrame(self.tempData1, columns = ['id', 'humidity'])
        self.df2 = pd.DataFrame(self.tempData2, columns = ['id', 'ph'])
        self.df3 = pd.DataFrame(self.tempData3, columns = ['id', 'light'])

        self.gFigure1 = plt.Figure(figsize = (6, 5), dpi = 69)
        self.gAx1 = self.gFigure1.add_subplot(111)
        self.gChartType1 = FigureCanvasTkAgg(self.gFigure1, self.graphRoot)
        self.gChartType1.get_tk_widget().pack(side = tk.LEFT, fill = tk.BOTH)
        self.df1 = self.df1[['id', 'humidity']].groupby('id').sum()
        self.df1.plot(kind = "bar", legend = True, ax = self.gAx1)
        self.gAx1.set_title("ID compared with humidity")

        self.gFigure2 = plt.Figure(figsize = (5, 4), dpi = 69)
        self.gAx2 = self.gFigure2.add_subplot(111)
        self.gChartType2 = FigureCanvasTkAgg(self.gFigure2, self.graphRoot)
        self.gChartType2.get_tk_widget().pack(side = tk.LEFT, fill = tk.BOTH)
        self.df2 = self.df2[["id", "ph"]].groupby("id").sum()
        self.df2.plot(kind = "line", legend = True, ax = self.gAx2, color = 'r', marker = 'o', fontsize = 10)
        self.gAx2.set_title("ID compared with acidity")

        self.gFigure3 = plt.Figure(figsize = (5, 4), dpi = 69)
        self.gAx3 = self.gFigure3.add_subplot(111)
        self.gAx3.scatter(self.df3['id'], self.df3['light'])
        self.gChartType3 = FigureCanvasTkAgg(self.gFigure3, self.graphRoot)
        self.gChartType3.get_tk_widget().pack(side = tk.LEFT, fill = tk.BOTH)
        self.gAx3.legend(['light'])
        self.gAx3.set_xlabel("ID")
        self.gAx3.set_title("ID compared with light level")

    
    def updateHomeGui(self):
        self.hideHomeGui()
        self.showHomeGui()

    def movePrevious(self):
        if self.curStep - 1 >= 0:
            self.curStep -= 1
        else:
            self.curStep = self.numPots - 1
        self.updateHomeGui()

    def moveNext(self):
        if self.curStep + 1 > self.numPots - 1:
            self.curStep = 0
        else:
            self.curStep += 1
        self.updateHomeGui()

    def calculateFontSize(self, guiName, defSize, text = ""):
        if text and len(text) > 0:
            if guiName == "flower_name":
                if len(text) <= 8:
                    return 14
                else:
                    return 11
            else:
                return defSize
        else:
            return defSize

    def calculateX(self, startX, width, text, fontSize):
        wordWidth = len(text) * (fontSize - 4)
        return startX + width / 2 - wordWidth / 2
   
    def hideEdit(self, who, id = ""):
        
        self.editEntry.place(x = -500)
        self.bgLbl.unbind("<Button-1>")
        xPos = 95

        if who == "flower_name":

            # If text has been edited
            if self.editEntryTxt.get() != self.nameLblTxt.get():
                
                # Update database
                self.db.execute(f"UPDATE user_pots SET name='{self.editEntryTxt.get()}' WHERE name='{self.nameLblTxt.get()}'")
                self.db.commit()
                
                # Update label to new name
                self.nameLblTxt.set(self.editEntryTxt.get())
                
                # Align it correctly after a new name
                nameFontSize = self.calculateFontSize("flower_name", 14, self.editEntryTxt.get())
                self.nameLbl.place(x = self.calculateX(xPos - 15, 137, self.editEntryTxt.get(), nameFontSize)) 
                
                print("Updated new flower name in database")

        elif who == "flower_desc":

            if self.editEntryTxt.get() != self.descLblTxt.get():

                # Update database
                self.db.execute(f"UPDATE user_pots SET desc='{self.editEntryTxt.get()}' WHERE id='{id}'")
                self.db.commit()

                # Update label to new name
                self.descLblTxt.set(self.editEntryTxt.get())

                # Align it correctly after a new desc
                self.descLbl.place(x = self.calculateX(xPos - 15, 137, self.editEntryTxt.get(), 8))

                print("Updated new flower description in database")

        self.currentlyEditing = False
        self.updateHomeGui()
    
    def editDetail(self, detail, id = ""):
        
        # Prevent multiple editing at once to prevent other edit entries not closing
        if self.currentlyEditing:
            return

        xPos = 95
        yPos = 100
        self.currentlyEditing = True
        if detail == "flower_name":
            self.editEntryTxt = tk.StringVar()
            self.editEntryTxt.set(self.nameLblTxt.get())
            self.editEntry = tk.Entry(self.secFrame, bg = self.root['bg'], textvariable = self.editEntryTxt)
            self.editEntry.place(x = xPos - 15, y = yPos + 120, width = 137, height = 25)
            self.bgLbl.bind("<Button-1>", lambda e: self.hideEdit("flower_name"))
        elif detail == "flower_desc":
            self.editEntryTxt = tk.StringVar()
            self.editEntryTxt.set(self.descLblTxt.get())
            self.editEntry = tk.Entry(self.secFrame, bg = self.root['bg'], textvariable = self.editEntryTxt)
            self.editEntry.place(x = self.calculateX(xPos - 15, 137, self.descLblTxt.get(), 8), y = yPos + 100 + 45, width = 80, height = 20)
            self.bgLbl.bind("<Button-1>", lambda e: self.hideEdit("flower_desc", id))
            
    def refreshHomeData(self, dontContinue = False):
        row = self.cursor.execute("SELECT * FROM user_pots")
        data = row.fetchall() # [(, , , , , ,), (, , , , , ,)]

        for x in data:
            try:
                if self.sensorData[x[0]]: # x[0] = id
                    pass
            except:
                self.sensorData[x[0]] = {}
            finally:
                self.sensorData[x[0]]["humidity"] = random.randint(43, 99) #99.9 - random.randint(0, 9) / 10
                self.sensorData[x[0]]["ph"] = 7.5 - random.randint(0, 10) / 10
                self.sensorData[x[0]]["light"] = random.randint(53, 99)

        self.initData = False
        self.lastTime = time.time()
        print("Refreshed current sensor data to new data")

        if not self.currentlyEditing:
            if self.curPage == "home":
                self.updateHomeGui()
        if not dontContinue:
            self.root.after(15000, self.refreshHomeData)


    def showHomeGui(self):
        row = self.cursor.execute("SELECT * FROM user_pots")
        data = row.fetchall() # [(, , , , , ,), (, , , , , ,)]
        self.numPots = len(data)

        # If theres nothing to draw, don't draw it obviously
        if self.numPots == 0:
            return

        #maxHeight = len(data) * 180
        #self.secFrame.configure(height = maxHeight)

        # Create sensor data if it doesn't exist
        if self.initData or (time.time() - self.lastTime) >= self.refreshTime:
            for x in data:
                try:
                    if self.sensorData[x[0]]: # x[0] = id
                        pass
                except:
                    self.sensorData[x[0]] = {}
                finally:
                    self.sensorData[x[0]]["humidity"] = random.randint(43, 99) #99.9 - random.randint(0, 9) / 10
                    self.sensorData[x[0]]["ph"] = 7.5 - random.randint(0, 10) / 10
                    self.sensorData[x[0]]["light"] = random.randint(53, 99)
            self.initData = False
            self.lastTime = time.time()
            print("Refreshed current sensor data to new data")

        pot = data[self.curStep]
        id, name, desc, favorite, flower, state = pot[0], pot[1], pot[2], pot[3], pot[4], pot[5]
        imgPath = ""
        xPos = 95
        yPos = 100

        if flower == "no":
            imgPath = "gui/upload_placeholder.png"
        else:
            imgPath = flower

        self.flowerImg_ = Image.open(imgPath) # maybe use try except finally
        if not self.flowerImg_:
            print(f"Failed to find flower image {imgPath}\nPot: {id} ({name})")
        else:
            self.flowerImg = ImageTk.PhotoImage(self.flowerImg_)
            self.flowerLbl = tk.Label(self.secFrame, image = self.flowerImg, bg = self.root['bg'])
            self.flowerLbl.place(x = xPos, y = yPos, width = 100, height = 100)



            self.flowerLbl.bind("<Button-1>", lambda e: self.addUploadImage(id))
            nameFontSize = self.calculateFontSize("flower_name", 14, name)
            self.nameLblTxt = tk.StringVar()
            self.nameLblTxt.set(name)
            self.nameLbl = tk.Label(self.secFrame, bg = self.root['bg'], textvariable = self.nameLblTxt, font = ('Arial', nameFontSize))
            self.nameLbl.place(x = self.calculateX(xPos - 15, 137, name, nameFontSize), y = yPos + 120)
            self.nameLbl.bind("<Button-1>", lambda e: self.editDetail("flower_name"))

            finalDesc = len(desc) == 0 and "No description" or desc
            self.descLblTxt = tk.StringVar()
            self.descLblTxt.set(finalDesc)
            self.descLbl = tk.Label(self.secFrame, bg = self.root['bg'], textvariable = self.descLblTxt, font = ('Arial', 8), fg = "#5c5c5c", wraplength = 137, justify = "left")
            self.descLbl.place(x = self.calculateX(xPos - 15, 137, finalDesc, 8), y = yPos + 100 + 45)
            self.descLbl.bind("<Button-1>", lambda e: self.editDetail("flower_desc", id))

            self.likeImg_ = Image.open(favorite == "no" and "gui/like.png" or "gui/like_fill.png")
            self.likeImg = ImageTk.PhotoImage(self.likeImg_)
            self.likeLbl = tk.Label(self.secFrame, image = self.likeImg, bg = self.root['bg'])
            #self.imgHomeLbl.bind("<Button-1>", lambda e: self.showPage("home"))
            self.likeLbl.bind("<Button-1>", lambda e: self.toggleFavorite(id, favorite, flower))
            self.likeLbl.place(x = xPos + 110, y = yPos + 5)

            self.graphImg_ = Image.open("gui/graph.png")
            self.graphImg = ImageTk.PhotoImage(self.graphImg_)
            self.graphLbl = tk.Label(self.secFrame, image = self.graphImg, bg = self.root['bg'])
            self.graphLbl.place(x = xPos + 110, y = yPos + 5 + 30)
            self.graphLbl.bind("<Button-1>", lambda e: self.openGraph(flower))

            self.trashImg_ = Image.open("gui/trash.png")
            self.trashImg = ImageTk.PhotoImage(self.trashImg_)
            self.trashLbl = tk.Label(self.secFrame, image = self.trashImg, bg = self.root['bg'])
            self.trashLbl.place(x = xPos + 110, y = yPos + 5 + 60)
            self.trashLbl.bind("<Button-1>", lambda e: self.deletePot(id))

            self.btnPrev = tk.Button(self.secFrame, bg = "#FF7BA9", text = "<-", command = self.movePrevious, fg = "white")
            self.btnPrev.place(x = xPos - 50, y = yPos + 120, height = 25)

            self.btnNext = tk.Button(self.secFrame, bg = "#FF7BA9", text = "->", command = self.moveNext, fg = "white")
            self.btnNext.place(x = xPos + 120, y = yPos + 120, height = 25)

            # Sensor data
            if flower != "no":
                self.idLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = f"ID: {id}", font = ('Arial', 8), fg = "#5c5c5c")
                self.idLbl.place(x = xPos - 45, y = yPos + 200)

                self.wetLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = f"Humidity: {round(self.sensorData[id]['humidity'], 2)}%", font = ('Arial', 8), fg = "#5c5c5c")
                self.wetLbl.place(x = xPos - 45, y = yPos + 230)

                self.phLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = f"Acidity: {self.sensorData[id]['ph']} pH", font = ('Arial', 8), fg = "#5c5c5c")
                self.phLbl.place(x = xPos + 60, y = yPos + 230)

                self.lightLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = f"Light level: {self.sensorData[id]['light']}%", font = ('Arial', 8), fg = "#5c5c5c")
                self.lightLbl.place(x = xPos - 45, y = yPos + 260)

                self.tempLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = f"Temperature: {self.weather.getTemp(True)} °C", font = ('Arial', 8), fg = "#5c5c5c")
                self.tempLbl.place(x = xPos + 60, y = yPos + 260)
            else:
                 self.idLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = "ID: Pot is empty", font = ('Arial', 8), fg = "#5c5c5c")
                 self.idLbl.place(x = xPos - 45, y = yPos + 200)               

            


    def hideHomeGui(self):
        try:
            self.flowerLbl.place(x = -500)
            self.nameLbl.place(x = -500)
            self.descLbl.place(x = -500)
            self.likeLbl.place(x = -500)
            self.graphLbl.place(x = -500)
            self.trashLbl.place(x = -500)
            self.btnPrev.place(x = -500)
            self.btnNext.place(x = -500)
            self.idLbl.place(x = -500)
            self.wetLbl.place(x = -500)
            self.phLbl.place(x = -500)
            self.lightLbl.place(x = -500)
            self.tempLbl.place(x = -500)
        except:
            pass
        try:
            if self.editEntry:
                self.editEntry.place(x = -500)
        except:
            pass

    def genPotID(self):
        first, second, third = str(random.randint(1, 999999)), str(random.randint(1, 999999)), str(random.randint(1, 999999))
        prefinal = f"PT-{first}-{second}-{third}"
        final = hashlib.md5(prefinal.encode("utf-8")).hexdigest()
        return final

    def hideAddStatusMsg(self):
        self.addStatusLbl.configure(text = "")

    def savePot(self):
        name = self.getAddName()
        if len(name) > 0:
            id = self.genPotID()
            desc = self.getAddDesc()
            favorite = "no"
            flower = "no"
            state = "prazno"

            self.db.execute(f"INSERT INTO user_pots(id, name, desc, favorite, flower, state) VALUES('{id}', '{name}', '{desc}', '{favorite}', '{flower}', '{state}')")
            self.db.commit()
            print(f"Pot saved in database.\n\nID: {id}\nName: {name}\nDescription: {desc}\nFavorite: {favorite}\nFlower: {flower}\nState: {state}")
            self.addPotNameTxt.set("")
            self.addPotDescTxt.set("")
            self.addStatusLbl.configure(fg = "#55cc55", text = "Pot successfully saved.")
            self.secFrame.after(3000, self.hideAddStatusMsg)
        else:
            self.addStatusLbl.configure(fg = "#ff0033", text = "Pot name is incorrect.")


    def showAddGui(self):

        # Pot image
        self.addPotImg_ = Image.open("gui/pot.png")
        self.addPotImg = ImageTk.PhotoImage(self.addPotImg_)
        self.addPotLbl = tk.Label(self.secFrame, image = self.addPotImg, bg = self.root['bg'])
        self.addPotLbl.place(x = 110, y = 110)

        # Pot name
        self.addPotNameTxt = tk.StringVar()
        self.addPotNameTxt.trace("w", self.limitNameEntry)
        self.addPotName = tk.Entry(self.secFrame, textvariable = self.addPotNameTxt, bg = self.root['bg'])
        self.addPotNameLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = "Name (max. 16 letters) *", font = ('Arial', 8))
        self.addPotName.place(x = 70, y = 210, height = 25)
        self.addPotNameLbl.place(x = 70, y = 190)

        # Pot description
        self.addPotDescTxt = tk.StringVar()
        self.addPotDesc = tk.Entry(self.secFrame, textvariable = self.addPotDescTxt, bg = self.root['bg'])
        self.addPotDescLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = "Description", font = ('Arial', 8))
        self.addPotDesc.place(x = 70, y = 260, height = 25)
        self.addPotDescLbl.place(x = 70, y = 240)

        # Save button
        self.addPotBtn = tk.Button(self.secFrame, bg = "#FF7BA9", fg = "white", text = "Save", command = lambda: self.savePot())
        self.addPotBtn.place(x = 110, y = 320, height = 25)

        # Save status message
        self.addStatusLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = "", fg = "#55cc55")
        self.addStatusLbl.place(x = 65, y = 350)

        # Advices
        self.addInfoImg_ = Image.open("gui/info.png")
        self.addInfoImg = ImageTk.PhotoImage(self.addInfoImg_)
        self.addInfoImgLbl = tk.Label(self.secFrame, image = self.addInfoImg, bg = "#fff4fa")
        self.addInfoLbl = tk.Label(self.secFrame, bg = "#fff4fa", fg = "#5c5c5c", text = "Adding, editing and deleting flowers or pots\ncan be done from the main menu.", font = ('Arial', 8))
        self.addInfoImgLbl.place(x = 20, y = 478)
        self.addInfoLbl.place(x = 50, y = 475)

    def hideAddGui(self):
        self.addPotLbl.place(x = -500)
        self.addPotName.place(x = -500)
        self.addPotNameLbl.place(x = -500)
        self.addPotDesc.place(x = -500)
        self.addPotDescLbl.place(x = -500)
        self.addPotBtn.place(x = -500)
        self.addStatusLbl.place(x = -500)
        self.addInfoImgLbl.place(x = -500)
        self.addInfoLbl.place(x = -500)

    def cleanHistory(self):
        self.hideHistoryGui()
        self.logs = {}
        self.showHistoryGui()

    def showHistoryGui(self):

        # Remove them since we'll recreate them again
        for element, nothing in self.logElements.items():
            try:
                element.place(x = -500)
            except:
                pass
        self.logElements = {}

        index = 1
        for timestamp, message in self.logs.items():
            lbl = tk.Label(self.secFrame, bg = "white", text = message, font = ('Arial', 7))
            yPos = 90 + (index * 25 - 25)
            lbl.place(x = 0, y = yPos)
            self.logElements[lbl] = True
            index += 1

        self.histRemBtn = tk.Button(self.secFrame, bg = "#ff0033", fg = "white", text = "Clear", command = lambda: self.cleanHistory())
        self.histRemBtn.place(x = 180, y = 38, width = 60, height = 30)

    def hideHistoryGui(self):
        # Remove them
        for element, nothing in self.logElements.items():
            try:
                element.place(x = -500)
            except:
                pass
        self.logElements = {}
        self.histRemBtn.place(x = -500)

    def doLogout(self):
        os.execv(sys.executable, ['python'] + sys.argv)

    def saveUserData(self):
        self.userData["adminName"] = self.settNameEntryTxt.get()
        self.userData["adminSurname"] = self.settSurnameEntryTxt.get()
        self.adminName = self.settNameEntryTxt.get()
        self.adminSurname = self.settSurnameEntryTxt.get()
        self.hideSettingsGui()
        self.showSettingsGui()
        try:
            with open("userdata.json", "w") as file_writer:
                json.dump(self.userData, file_writer)
                print("User data saved")
        except:
            print("Unable to save userdata.json for unknown reason.")


    def showSettingsGui(self):
        
        self.settProfileImg_ = Image.open("gui/user.png")
        self.settProfileImg = ImageTk.PhotoImage(self.settProfileImg_)
        self.settProfileLbl = tk.Label(self.secFrame, bg = self.root['bg'], image = self.settProfileImg)
        self.settProfileLbl.place(x = 10, y = 90)

        self.settProfileNameLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = f"{self.curUser} ({self.adminName} {self.adminSurname})", font = ('Arial', 11))
        self.settProfileNameLbl.place(x = 50, y = 94)

        self.settProfileLogoutBtn = tk.Button(self.secFrame, bg = "#ff0033", fg = "white", text = "Logout", command = self.doLogout)
        self.settProfileLogoutBtn.place(x = 220, y = 90, width = 60, height = 30)

        self.settNameEntryTxt = tk.StringVar()
        self.settNameEntryTxt.set(self.adminName)
        self.settNameEntry = tk.Entry(self.secFrame, bg = self.root['bg'], textvariable = self.settNameEntryTxt)
        self.settNameEntry.place(x = 75, y = 200, width = 150, height = 30)

        self.settNameEntryLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = "Name", font = ('Arial', 8), fg = "#5c5c5c")
        self.settNameEntryLbl.place(x = 75, y = 180)

        self.settSurnameEntryTxt = tk.StringVar()
        self.settSurnameEntryTxt.set(self.adminSurname)
        self.settSurnameEntry = tk.Entry(self.secFrame, bg = self.root['bg'], textvariable = self.settSurnameEntryTxt)
        self.settSurnameEntry.place(x = 75, y = 260, width = 150, height = 30)

        self.settSurnameEntryLbl = tk.Label(self.secFrame, bg = self.root['bg'], text = "Surname", font = ('Arial', 8), fg = "#5c5c5c")
        self.settSurnameEntryLbl.place(x = 75, y = 240)

        self.settSaveBtn = tk.Button(self.secFrame, bg = "#FF7BA9", fg = "white", text = "Save", command = lambda: self.saveUserData())
        self.settSaveBtn.place(x = 75, y = 300, width = 150, height = 30)

    def hideSettingsGui(self):
        self.settProfileLbl.place(x = -500)
        self.settProfileNameLbl.place(x = -500)
        self.settProfileLogoutBtn.place(x = -500)
        self.settNameEntry.place(x = -500)
        self.settNameEntryLbl.place(x = -500)
        self.settSurnameEntry.place(x = -500)
        self.settSurnameEntryLbl.place(x = -500)
        self.settSaveBtn.place(x = -500)

    def showFavoriteGui(self):
        row = self.cursor.execute(f"SELECT * FROM user_pots WHERE favorite='yes'")
        data = row.fetchall()
        for x in range(len(data)):
            curPot = data[x]
            id, name, desc, favorite, flower, state = curPot[0], curPot[1], curPot[2], curPot[3], curPot[4], curPot[5]
            if flower != "no":
                yPos = 100 + (50 * (x+1)) - 50
                self.favElements[id + "_img_"] = Image.open(flower)
                self.favElements[id + "_img_resized"] = self.favElements[id + "_img_"].resize((40, 40))
                self.favElements[id + "_img"] = ImageTk.PhotoImage(self.favElements[id + "_img_resized"])
                self.favElements[id + "_lbl"] = tk.Label(self.secFrame, bg = self.root['bg'], image = self.favElements[id + "_img"])
                self.favElements[id + "_lbl"].place(x = 10, y = yPos, width = 40, height = 40)

                self.favElements[id + "namelbl"] = tk.Label(self.secFrame, bg = self.root['bg'], font = ('Arial', 10), text = name)
                self.favElements[id + "namelbl"].place(x = 60, y = yPos)
                self.favElements[id + "desclbl"] = tk.Label(self.secFrame, bg = self.root['bg'], font = ('Arial', 8), text = desc, fg = "#5c5c5c")
                self.favElements[id + "desclbl"].place(x = 60, y = yPos + 25)


    def hideFavoriteGui(self):
        for index, element in self.favElements.items():
            try:
                element.place(x = -500)
            except:
                pass
        self.favElements = {}

    def showBiljkeGUI(self):
        self.curPage = "home"
        self.navHeight = 40

        self.mainFrame = tk.Frame(self.root, width = self.width, height = self.height - self.navHeight)
        self.mainFrame.place(x = 0, y = 0)

        self.mainCanvas = tk.Canvas(self.mainFrame, width = self.width, height = self.height- self.navHeight)
        self.mainCanvas.place(x = 0, y = 0, height = self.height- self.navHeight)

        self.scrollBar = tk.Scrollbar(self.mainFrame, orient = VERTICAL, command = self.mainCanvas.yview)
        self.scrollBar.place(x = self.width - 15, y = 0, height = self.height- self.navHeight)

        self.mainCanvas.configure(yscrollcommand = self.scrollBar.set)
        self.mainCanvas.bind("<Configure>", lambda e: self.mainCanvas.configure(scrollregion = self.mainCanvas.bbox("all")))

        self.secFrame = tk.Frame(self.mainCanvas, width = self.width, height = self.height- self.navHeight, bg = self.root['bg'])
        self.secFrame.place(x = 0, y = 0)

        self.mainCanvas.create_window((0, 0), window = self.secFrame, anchor = "nw")

        self.bg_ = Image.open("gui/background.png")
        self.bg = ImageTk.PhotoImage(self.bg_)
        self.bgLbl = tk.Label(self.secFrame, image = self.bg)
        self.bgLbl.place(x = 0, y = 0, width = self.width, height = self.height)

        self.c1 = Canvas(self.root, width = self.width, height = self.navHeight, bg = "white")
        self.c1.place(x = 0, y = self.height - self.navHeight)
        self.c1.create_rectangle(0, 0, self.width, self.navHeight, outline = "#FFFFFF")

        # Home Button
        self.imgHome_ = Image.open("gui/home.png")
        self.imgHome = ImageTk.PhotoImage(self.imgHome_)
        self.imgHomeLbl = tk.Label(self.root, image = self.imgHome, bg = "white")
        self.imgHomeLbl.place(x = 20, y = self.height - self.navHeight + 8, width = 24, height = 24)
        self.imgHomeLbl.bind("<Button-1>", lambda e: self.showPage("home"))

        # Favorites Button
        self.imgFav_ = Image.open("gui/favorites.png")
        self.imgFav = ImageTk.PhotoImage(self.imgFav_)
        self.imgFavLbl = tk.Label(self.root, image = self.imgFav, bg = "white")
        self.imgFavLbl.place(x = 79, y = self.height - self.navHeight + 8, width = 24, height = 24)
        self.imgFavLbl.bind("<Button-1>", lambda e: self.showPage("favorites"))

        # Add Button
        self.imgAdd_ = Image.open("gui/add.png")
        self.imgAdd = ImageTk.PhotoImage(self.imgAdd_)
        self.imgAddLbl = tk.Label(self.root, image = self.imgAdd, bg = "white")
        self.imgAddLbl.place(x = 139, y = self.height - self.navHeight + 8, width = 24, height = 24)
        self.imgAddLbl.bind("<Button-1>", lambda e: self.showPage("add"))

        # History Button
        self.imgHist_ = Image.open("gui/history.png")
        self.imgHist = ImageTk.PhotoImage(self.imgHist_)
        self.imgHistLbl = tk.Label(self.root, image = self.imgHist, bg = "white")
        self.imgHistLbl.place(x = 199, y = self.height - self.navHeight + 6, width = 28, height = 28)
        self.imgHistLbl.bind("<Button-1>", lambda e: self.showPage("history"))
        if self.historyNew:
            self.imgHistNew_ = Image.open("gui/notification.png")
            self.imgHistNew = ImageTk.PhotoImage(self.imgHistNew_)
            self.imgHistNewLbl = tk.Label(self.root, bg = "white", image = self.imgHistNew)
            self.imgHistNewLbl.place(x = 218, y = self.height - self.navHeight + 2, width = 12, height = 12)

        # Settings Button
        self.imgSett_ = Image.open("gui/settings.png")
        self.imgSett = ImageTk.PhotoImage(self.imgSett_)
        self.imgSettLbl = tk.Label(self.root, image = self.imgSett, bg = "white")
        self.imgSettLbl.place(x = 255, y = self.height - self.navHeight + 5)
        self.imgSettLbl.bind("<Button-1>", lambda e: self.showPage("settings"))

        # Current position label
        self.c2 = Canvas(self.root, width = 60, height = 3, bg = "#FF7BA9")
        self.c2.place(x = 0, y = self.height - self.navHeight)
        self.c2.create_rectangle(0, 0, 60, 3, outline="#FF7BA9")

        self.lblCategory = tk.Label(self.secFrame, text = f"Your pots", bg = self.root['bg'], font = ('Comic Sans', 20))
        self.lblCategory.place(x = 30, y = 30)
        
        self.showHomeGui()


def main():
    root = tk.Tk()
    myApp = PyFlowerPots(root)
    root.mainloop()

main()