import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3

#EXTRACTING TEXT FROM IMAGE
def image_to_txt(path):
  input_img=Image.open(path)

  #CONVERTING IMAGE TO ARRAY
  image_arr=np.array(input_img)

  reader=easyocr.Reader(['en'])#languGE
  text=reader.readtext(image_arr,detail=0)

  return text,input_img


#CONVERTING THE EXTRACTED TEXT TO DICTIONARY FOR DATAFRAME CONVERTION
def extracted_text(texts):

  extrd_dict={"name":[],"designation":[],"company_name":[],"contactno":[],"email":[],"website":[],"address":[],"pincode":[]}
  extrd_dict['name'].append(texts[0])
  extrd_dict['designation'].append(texts[1])
  for i in range(2,len(texts)):#WILL RUN FOR THE NUM OF TIMES THE DATA IS PRESENT

   if texts[i].startswith("+") or(texts[i].replace("-","").isdigit()and "-" in texts[i]):

    extrd_dict['contactno'].append(texts[i])

   elif "@" in texts[i] and".com" in texts[i]:

    extrd_dict["email"].append(texts[i])

   elif"WWW" in texts[i] or "www" in texts[i]or"Www"in texts[i] or"wWw"in texts[i] or"wwW"in texts[i]:

      sml=texts[i].lower()

      extrd_dict["website"].append(sml)

   elif "TamilNadu" in texts[i] or "Tamil Nadu" in texts[i] or texts[i].isdigit():
    extrd_dict["pincode"].append(texts[i])

   elif re.match(r'^[A-Za-z]',texts[i]):
    extrd_dict["company_name"].append(texts[i])

   else:
    remove_colon=re.sub(r'[,;]',"",texts[i])
    extrd_dict["address"].append(remove_colon)


  for key,value in extrd_dict.items():
    if len(value)>0:
      concardenate=" ".join(value)
      extrd_dict[key]=[concardenate]

    else:
      value="NA"
      extrd_dict[key]=[value]

  return extrd_dict



#STREAMLIT PART

#HEADING

st.set_page_config(layout="wide")
st.title("Extracting Business Card Data With OCR")

#SIDEBAR
with st.sidebar:
  select=option_menu("Main menu",["HOME","UPLOAD AND MODIFY","DELETE"])

#SIDEBAR OPTION1 "HOME"(EXPLAINS THIS APPLICATION)
if select=="HOME":
  st.markdown("### :red[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
  st.write("")
  st.write("")
  st.write(
            "### :blue[**About :**] This is a Python application designed to extract information from business card images.")
  st.write("")
  st.write("")
  st.write("")
  st.write("")
  st.write("### :green[**Swipe left to explore the features of this application**]")

#SIDEBAR OPTION1 "UPLOAD AND MODIFY"(UPLOAD HELPS US TO UPLOAD THE IMAGE AND EXTRACT THE DETAILS)
elif select=="UPLOAD AND MODIFY":
  img=st.file_uploader("Upload the image",type=["png","jpg","jpeg"])#UPLOAD IMAGE

  if img is not None:
    st.image(img,width=300)

    text_image,input_img=image_to_txt(img)

    text_dict = extracted_text(text_image)#EXTRACT THE DETAILS

    if text_dict:
      st.success("TEXT EXTRACTED SUCCESSFULLY")

    df=pd.DataFrame(text_dict)

    #CONVERTING IMAGE TO BYTES
    image_bytes=io.BytesIO()
    input_img.save(image_bytes,format="PNG")

    image_data=image_bytes.getvalue()

    #CREATING DICTIONARY
    data={"image":[image_data]}

    df_1=pd.DataFrame(data)

    concaddf=pd.concat([df,df_1],axis=1)#axis=0 row cancat  axis=1 column
    st.dataframe (concaddf)

    button1=st.button("Save",use_container_width=True)


    if button1:
      
      #SQL CONNECTION
      mydb=sqlite3.connect("bizcardx.db")
      cursor=mydb.cursor()

      #CREATING TABLE
      create_table_query='''CREATE TABLE IF NOT EXISTS bizcard_details(name varchar(255),
                                                                      designation	varchar(255),
                                                                      company_name	varchar(255),
                                                                      contactno	varchar(255),
                                                                      email	varchar(255),
                                                                      website	varchar(255),
                                                                      address	varchar(255),
                                                                      pincode	varchar(255),
                                                                      image	varchar(255))'''
      cursor.execute(create_table_query)
      mydb.commit()

      #INSERT TABLE
      insert_query='''INSERT INTO bizcard_details(name,designation,company_name,contactno,email,
                                                  website,address,pincode,image)

                                                  values(?,?,?,?,?,?,?,?,?)'''
      datas=concaddf.values.tolist()[0]
      cursor.execute(insert_query,datas)
      mydb.commit()

      st.success("saved successfully")
  
  #RADIO BUTTON
  method=st.radio("select the method",["None",'Preview',"Modify"])

  if method=="None":
    st.write("")

  if method=="Preview":
    mydb=sqlite3.connect("bizcardx.db")
    cursor=mydb.cursor()

    #SELECT QUERY
    select_query="select * from bizcard_details "

    cursor.execute(select_query)
    table=cursor.fetchall()
    mydb.commit()

    table_df=pd.DataFrame (table,columns=("name","designation","company_name","contactno","email",
                                                "website","address","pincode","image"))
    st.dataframe(table_df)

  elif method=="Modify":# TO MODIFY THE DETAILS ONE BY ONE IF NEEDED 
    mydb=sqlite3.connect("bizcardx.db")
    cursor=mydb.cursor()

    #SELECT QUERY
    select_query="select * from bizcard_details "
    cursor.execute(select_query)
    table=cursor.fetchall()
    mydb.commit()

    table_df=pd.DataFrame (table,columns=("name","designation","company_name","contactno","email",
                                                "website","address","pincode","image"))

    col1,col2=st.columns(2)
    with col1:

      selected_name=st.selectbox("select the name",table_df["name"])# BY SELECTING THE NAME ALL THE DETAILS OF THAT SELECTED PERSON WILL BE DISPLAYED

    df3=table_df[table_df["name"]==selected_name]

    df4=df3.copy()

    col1,col2=st.columns(2)
    with col1:
      mo_name=st.text_input("name",df3['name'].unique()[0])
      mo_desig=st.text_input("designation",df3['designation'].unique()[0])
      mo_comp_name=st.text_input("company_name",df3['company_name'].unique()[0])
      mo_contact=st.text_input("contactno",df3['contactno'].unique()[0])
      mo_email=st.text_input("email",df3['email'].unique()[0])

      df4["name"]=mo_name
      df4["designation"]=mo_desig
      df4["company_name"]=mo_comp_name
      df4["contactno"]=mo_contact
      df4["email"]=mo_email

    with col2:
      mo_web=st.text_input("website",df3['website'].unique()[0])
      mo_add=st.text_input("address",df3['address'].unique()[0])
      mo_pinc=st.text_input("pincode",df3['pincode'].unique()[0])
      mo_img=st.text_input("image",df3['image'].unique()[0])

      df4["website"]=mo_web
      df4["address"]=mo_add
      df4["pincode"]=mo_pinc
      df4["image"]=mo_img

    st.dataframe(df4)

    col1,col2=st.columns(2)
    with col1:
      button3=st.button("Modify")

    if button3:

      mydb=sqlite3.connect("bizcardx.db")
      cursor=mydb.cursor()

      cursor.execute(f"DELETE FROM bizcard_details where name ='{selected_name}'")
      mydb.commit()


      #INSERT TABLE
      insert_query='''INSERT INTO bizcard_details(name,designation,company_name,contactno,email,
                                                  website,address,pincode,image)

                                                  values(?,?,?,?,?,?,?,?,?)'''
      datas=df4.values.tolist()[0]
      cursor.execute(insert_query,datas)
      mydb.commit()

      st.success("modified successfully")

elif select=="DELETE":# TO DELETE DETAILS WHICH ARE PRESENT IN THE DATABASE
  #SELECT QUERY
  mydb=sqlite3.connect("bizcardx.db")
  cursor=mydb.cursor()

  col1,col2=st.columns(2)

  with col1:
    select_query="select name from bizcard_details "

    cursor.execute(select_query)
    table1=cursor.fetchall()
    mydb.commit()

    names=[]

    for i in table1:#all datas will b in tuple
      names.append(i[0])


    nameselect=st.selectbox("select the name",names)


  with col2:
    select_query1=f"select designation from bizcard_details where name='{nameselect}'"

    cursor.execute(select_query1)
    table2=cursor.fetchall()
    mydb.commit()

    designations=[]

    for j in table2:#all datas will b in tuple
      designations.append(j[0])


    designationselect=st.selectbox("select the designation",designations)

  if nameselect and designationselect:
    col1,col2,col3=st.columns(3)

    with col1:
      st.write(f"select name : {nameselect}")#SELECT NAME
      st.write("")
      st.write("")
      st.write("")
      st.write(f"select designation : {designationselect}")#SELECT DESIGNATION OF THE PERSON WHOES DATA HAS TO BE DELETED

    with col2:
      st.write("")
      st.write("")
      st.write("")
      st.write("")

      remove=st.button("delete")#DELETE BUTTON

      if remove:
        cursor.execute(f"Delete from bizcard_details WHERE name='{nameselect}'and designation ='{designationselect}' ")
        mydb.commit()

        st.warning("Deleted")#WARNING MESSAGE INDICATING DATA IS DELETED




  
 







