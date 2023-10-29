import json
import datetime
import os
import sys
from datetime import date
import requests
from pathlib import Path
from tkinter import *
from PIL import Image,ImageTk, ImageDraw, ImageFont

def get_lat_lon_from_ip():
    lres = requests.get("http://ip-api.com/json/?fields=lat,lon")
    rd = lres.json()
    return rd["lat"], rd["lon"]

#Config
def get_config(): #obtenir parametres pour requête
	res = []
	file = open(f'{Path(__file__).parent}/config.json','r') #config.json
	data = json.load(file)
	lat = data['latitude']
	lng = data['longitude']
	if lat == 0 and lng == 0:
		lat, lon = get_lat_lon_from_ip()
	res.append(lat)
	res.append(lng)
	file.close()
	date =datetime.date.today()
	res.append(date)
	res.append(date + datetime.timedelta(days = 4))
	res.append(int(datetime.datetime.now().strftime("%H")))
	return res #latitude,longitude,date_debut(date du jour),date de fin, heure actuel

config = get_config()

#Requete get data meteo
api =f"""https://api.open-meteo.com/v1/forecast?latitude={config[0]}&longitude={config[1]}&hourly=temperature_2m,apparent_temperature,weathercode&daily=temperature_2m_max,temperature_2m_min&timezone=auto&start_date={config[2]}&end_date={config[3]}"""
requete = requests.get(api)
reponse_json = requete.json()

#format : code api, texte ui, nom fichier à utiliser
code_meteo = [(0,"Clair","soleil"),(1,"Clair","soleil"),(2,"Couvert","couvert"),(3,"Couvert","couvert"),(45,"Brouillard","brouillard"),(48,"Brouillard","brouillard"),(51,"Bruine","pluie"),(53,"Bruine","pluie"),(55,"Bruine","pluie"),(56,"Bruine","pluie"),(57,"Bruine","pluie"),(61,"pluie faible","pluie"),(63,"pluie modere","pluie"),(65,"pluie forte","pluie"),(66,"pluie faible","pluie"),(67,"pluie forte","pluie"),(71,"neige legere","neige"),(73,"neige modere","neige"),(75,"neige forte","neige"),(77,"grele","grele"),(80,"pluie faible","pluie"),(81,"pluie modere","pluie"),(82,"pluie forte","pluie"),(85,"neige legere","neige"),(86,"neige forte","neige"),(95,"orage","tonerre"),(96,"orage & grele","tonerre"),(99,"orage & grele","tonerre")]

#Data météo
res_rtemp=reponse_json['hourly']['temperature_2m']#patern temperature reel
res_ftemp=reponse_json['hourly']['apparent_temperature']#patern temperature ressentie
res_whcode=reponse_json['hourly']['weathercode']#patern code météo par heure

#format : température reel date : 6h,12h,16h,22h,température ressentie(meme h)
temp_today = [res_rtemp[6],res_rtemp[12],res_rtemp[16],res_rtemp[22],res_ftemp[6],res_ftemp[12],res_ftemp[16],res_ftemp[22]]#j
temp_t1= [res_rtemp[30],res_rtemp[36],res_rtemp[40],res_rtemp[46],res_ftemp[30],res_ftemp[36],res_ftemp[40],res_ftemp[46]]#j+1
temp_t2= [res_rtemp[54],res_rtemp[60],res_rtemp[64],res_rtemp[70],res_ftemp[54],res_ftemp[60],res_ftemp[64],res_ftemp[70]]#j+2
temp_t3= [res_rtemp[78],res_rtemp[84],res_rtemp[88],res_rtemp[94],res_ftemp[78],res_ftemp[84],res_ftemp[88],res_ftemp[94]]#j+3
temp_t4= [res_rtemp[102],res_rtemp[108],res_rtemp[112],res_rtemp[118],res_ftemp[102],res_ftemp[108],res_ftemp[112],res_ftemp[118]]#j+4

#code météo
def get_wjcode(jour):#obtenir le code météo le plus utilisé entre 6h et 22h (marche uniquement de j+1 à j+4)
	mem={}
	if jour == 1:
		interval = (24+6,47-1)
	elif jour == 2:
		interval = (48+6,71-1)
	elif jour == 3:
		interval = (72+6,95-1)
	elif jour == 4:
		interval = (96+6,119-1)
	for i in range(interval[0],(interval[1]+1)):
		if res_whcode[i] in mem:
			mem[res_whcode[i]]+=1
		else:
			mem[res_whcode[i]]=1
	return max(mem, key=mem.get)#renvoie la clé qui a la plus grande valeur

met_today = (res_whcode[6],res_whcode[12],res_whcode[16],res_whcode[22]) #6h,12h,16h,22h

temp_actuel = res_rtemp[config[4]]#température actuel
rtemp_actuel = res_ftemp[config[4]]#température ressentie actuel
met_actuel = res_whcode[config[4]]#code météo actuel

def get_data_show(code):#renvoie le nom du png et le temps à afficher  selon le code météo en argument
	for i in code_meteo:
		if i[0]==code:
			return (i[2],i[1])#nom png, texte temps


#limite ° ajd
temp_max=reponse_json["daily"]["temperature_2m_max"][0]
temp_min=reponse_json["daily"]["temperature_2m_min"][0]


def translate(jour,mois=None): #jour anglais -> francais
	trad_j = {"Monday": "Lundi","Tuesday": "Mardi","Wednesday": "Mercredi","Thursday": "Jeudi","Friday": "Vendredi","Saturday": "Samedi","Sunday": "Dimanche"}
	if mois is not None:
		trad_m = {"January": "Janvier","February": "Février","March": "Mars","April": "Avril","May": "Mai","June": "Juin","July": "Juillet","August": "Août","September": "Septembre","October": "Octobre","November": "Novembre","December": "Décembre"}
		return [trad_j[jour],trad_m[mois]]
	return (trad_j[jour])

#Get nom jour format ajd,j+1,...,j+4 + traduit en francais
jours = []
for i in range(5):
	jours.append(translate((config[2]+ datetime.timedelta(days = i)).strftime("%A")))
#date actuel
actual_date = translate(config[2].strftime("%A"),config[2].strftime("%B"))+[config[2].strftime("%d")]

#renvoie la moyenne d'une liste
def moyenne(liste):
    res=0
    for i in liste:
        res+=i
    return res/(len(liste))

#Ui
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path("./assets")


def relative_to_assets(path):
	path = os.path.join(*path.split("\\"))
	return ASSETS_PATH / Path(path)


window = Tk()
window.geometry("1280x720")
window.configure(bg = "#111111")
window.title("Projet météo")
if ( sys.platform.startswith('win')):
	window.iconbitmap(relative_to_assets("application-meteo.ico"))
else:
	window.iconbitmap(f"@{relative_to_assets('application-meteo.xbm')}")


canvas = Canvas(
    window,
    bg = "#212121",
    height = 720,
    width = 1280,
    bd = 0,
    highlightthickness = 0,
    relief = "ridge"
)

canvas.place(x = 0, y = 0)

#rectangles arrondi
image_image_1 = PhotoImage(
    file=relative_to_assets("background.png"))
image_1 = canvas.create_image(
    648.0,
    364.0,
    image=image_image_1
)

#initialisation custom font
background_texte = Image.open(relative_to_assets('vide.png'))
draw = ImageDraw.Draw(background_texte)
text_color = 'rgb(255, 255, 255)'

#draw  textes
#température mini
font = ImageFont.truetype(str(relative_to_assets('font\\inter-light-italic.otf')), size=35)
draw.text((616.0, 81.0), f"{temp_min}°", fill=text_color, font=font)

font = ImageFont.truetype(str(relative_to_assets('font\\Inter-ThinItalic.otf')), size=26)
draw.text((610.0, 53.0), "MIN", fill=text_color, font=font)

#temperature max
font = ImageFont.truetype(str(relative_to_assets('font\\inter-light-italic.otf')), size=35)
draw.text((605.0, 230.0), f"{temp_max}°", fill=text_color, font=font)

font = ImageFont.truetype(str(relative_to_assets('font\\Inter-ThinItalic.otf')), size=26)
draw.text((608.0, 192.0), "MAX", fill=text_color, font=font)

#ressentie actuel
font = ImageFont.truetype(str(relative_to_assets('font\\inter-light-italic.otf')), size=35)
draw.text((318.0, 230.0), f"{rtemp_actuel}°", fill=text_color, font=font)

font = ImageFont.truetype(str(relative_to_assets('font\\Inter-ThinItalic.otf')), size=26)
draw.text((318.0, 200.0), "RESSENTIE", fill=text_color, font=font)

#texte meteo actuel
font = ImageFont.truetype(str(relative_to_assets('font\\Inter-Light.otf')), size=50)
draw.text((83.0, 293.0), get_data_show(met_actuel)[1], fill=text_color, font=font)

font = ImageFont.truetype(str(relative_to_assets('font\\Inter-Thin.otf')), size=26)
draw.text((817.0, 53.0), "MATIN", fill=text_color, font=font)

draw.text((1081.0, 53.0), "MIDI", fill=text_color, font=font)

draw.text((816.0, 196.0), "APREM", fill=text_color, font=font)

draw.text((1081.0, 196.0), "SOIR", fill=text_color, font=font)

#température reel matin
font1 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Thin.otf')), size=38)
draw.text((812.0, 78.0), f"{str(temp_today[0])}°", fill=text_color, font=font1)

font2 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Thin.otf')), size=16)
draw.text((812.0, 124.0), "RESSENTIE", fill=text_color, font=font2)

#températre ressentie matin
font3 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Thin.otf')), size=24)
draw.text((812.0, 143.0), f"{str(temp_today[4])}°", fill=text_color, font=font3)

#température reel midi
draw.text((1081.0, 78.0), f"{str(temp_today[1])}°", fill=text_color, font=font1)

draw.text((1081.0, 124.0), "RESSENTIE", fill=text_color, font=font2)

#températre ressentie midi
draw.text((1081.0, 143.0), f"{str(temp_today[5])}°", fill=text_color, font=font3)

#température reel aprem
draw.text((812.0, 229.0), f"{str(temp_today[2])}°", fill=text_color, font=font1)

draw.text((812.0, 274.0), "RESSENTIE", fill=text_color, font=font2)

#températre ressentie aprem
draw.text((812.0, 294.0), f"{str(temp_today[6])}°", fill=text_color, font=font3)

#température reel soir
draw.text((1081.0, 229.0), f"{str(temp_today[3])}°", fill=text_color, font=font1)

draw.text((1081.0, 274.0), "RESSENTIE", fill=text_color, font=font2)

#températre ressentie soir
draw.text((1081.0, 294.0), f"{str(temp_today[7])}°", fill=text_color, font=font3)

#date du jour
font = ImageFont.truetype(str(relative_to_assets('font\\Inter-Light.otf')), size=42)
draw.text((450.0, 362.0), f"{actual_date[0]} {actual_date[2]} {actual_date[1]}", fill=text_color, font=font)

#température reel j+1
font1 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Thin.otf')), size=53)
draw.text((252.0, 431.0), f"{round(moyenne(temp_t1[:4]),1)}°", fill=text_color, font=font1)#arrondi à 0,1 de la moyenne des températures réels de 6h,12h,16h,22h

#températre ressentie j+1
font2 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Light.otf')), size=24)
draw.text((245.0, 524.0), f"{round(moyenne(temp_t1[4:]),1)}°", fill=text_color, font=font2)#arrondi à 0,1 de la moyenne des températures ressentie de 6h,12h,16h,22h

font3 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Thin.otf')), size=24)
draw.text((245.0, 495.0), "RESSENTIE", fill=text_color, font=font3)

#jour haut gauche
font4 = ImageFont.truetype(str(relative_to_assets('font\\Inter-Light.otf')), size=32)
draw.text((411.0, 471.0), jours[1], fill=text_color, font=font4)

#température reel j+2
draw.text((814.0, 431.0), f"{round(moyenne(temp_t2[:4]),1)}°", fill=text_color, font=font1)#arrondi à 0,1 de la moyenne des températures réels de 6h,12h,16h,22h

#températre ressentie j+2
draw.text((808.0, 524.0), f"{round(moyenne(temp_t2[4:]),1)}°", fill=text_color, font=font2)#arrondi à 0,1 de la moyenne des températures ressentie de 6h,12h,16h,22h

draw.text((808.0, 495.0), "RESSENTIE", fill=text_color, font=font3)

#jour haut droite
draw.text((974.0, 471.0), jours[2], fill=text_color, font=font4)

#température reel j+3
draw.text((252.0, 560.0), f"{round(moyenne(temp_t3[:4]),1)}°", fill=text_color, font=font1)

#températre ressentie j+3
draw.text((245.0, 654.0), f"{round(moyenne(temp_t3[4:]),1)}°", fill=text_color, font=font2)

draw.text((245.0, 624.0), "RESSENTIE", fill=text_color, font=font3)

#jour bas gauche
draw.text((411.0, 600.0), jours[3], fill=text_color, font=font4)

#température reel j+4
draw.text((814.0, 569.0), f"{round(moyenne(temp_t4[:4]),1)}°", fill=text_color, font=font1)

#températre ressentie j+4
draw.text((808.0, 654.0), f"{round(moyenne(temp_t4[4:]),1)}°", fill=text_color, font=font2)

draw.text((808.0, 624.0), "RESSENTIE", fill=text_color, font=font3)

#jour bas droite
draw.text((974.0, 600.0), jours[4], fill=text_color, font=font4)

#température actuel
font = ImageFont.truetype(str(relative_to_assets('font\\Inter-ThinItalic.otf')), size=110)
draw.text((318.0, 53.0), f"{temp_actuel}°", fill=text_color, font=font)

draw_textes = ImageTk.PhotoImage(background_texte)
canvas.create_image(0, 0, image=draw_textes, anchor=NW)

canvas.create_rectangle(
    972.9646606445312,
    39.0,
    974.6083984375,
    325.26446533203125,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    701.999267578125,
    179.0,
    1245.0107421875,
    180.0,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    50.33363723754883,
    556.6536254882812,
    1227.3336372375488,
    557.6536254882812,
    fill="#FFFFFF",
    outline="")

canvas.create_rectangle(
    639.0,
    426.0,
    640.0,
    689.0,
    fill="#FFFFFF",
    outline="")

#ui -> image

#reduire la taille de l'image
def resize(nom,taille):
	if taille == 1:#images en haut à droite
		taille=65
	else: #images en haut à gauche
		taille = 105
	with Image.open(relative_to_assets(f'{nom}.png')) as im:
	    resized = im.resize((taille,taille))
	return resized #image avec les bonnes dimension


#image meteo actuel
im_now = ImageTk.PhotoImage(Image.open(relative_to_assets(f'{get_data_show(met_actuel)[0]}.png')))
canvas.create_image(83.34, 54.99, image=im_now, anchor=NW)


#image top right (matin)
im_tr6 = ImageTk.PhotoImage(resize(get_data_show(met_today[0])[0],1))
canvas.create_image(728, 80, image=im_tr6, anchor=NW)

#image top right (midi)
im_tr12 = ImageTk.PhotoImage(resize(get_data_show(met_today[1])[0],1))
canvas.create_image(999, 80, image=im_tr12, anchor=NW)

#image top right (aprem)
im_tr16 = ImageTk.PhotoImage(resize(get_data_show(met_today[2])[0],1))
canvas.create_image(728, 215, image=im_tr16, anchor=NW)

#image top right (soir)
im_tr22 = ImageTk.PhotoImage(resize(get_data_show(met_today[3])[0],1))
canvas.create_image(999, 215, image=im_tr22, anchor=NW)


#image bottom (j+1)
im_j1 = ImageTk.PhotoImage(resize(get_data_show(get_wjcode(1))[0],2))
canvas.create_image(107.02, 439.64, image=im_j1, anchor=NW)

#image bottom (j+2)
im_j2 = ImageTk.PhotoImage(resize(get_data_show(get_wjcode(2))[0],2))
canvas.create_image(107.02, 569.31, image=im_j2, anchor=NW)

#image bottom (j+3)
im_j3 = ImageTk.PhotoImage(resize(get_data_show(get_wjcode(3))[0],2))
canvas.create_image(673.18, 439.64, image=im_j3, anchor=NW)

#image bottom (j+4)
im_j4 = ImageTk.PhotoImage(resize(get_data_show(get_wjcode(4))[0],2))
canvas.create_image(673.18, 569.31, image=im_j4, anchor=NW)

window.resizable(False, False)
window.mainloop()
