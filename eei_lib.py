import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os

def azami (dosya, groupby = "Q", minQ = 0.01, minH = 0.01, minPhyd = 0.01):
    df = pd.read_excel("constant_rev/"+dosya,index_col=0)
    df = df.rename(columns={"Flow_Rate":"Q","Valve_Aperture":"D","Head":"H","Hydraulic_Power":"Phyd", \
                       "Suction_Pressure":"P1","Discharge_Pressure":"P2","Active_Power":"Pcons"})
    df = df.groupby(groupby,as_index=False).mean()
    df = df[df.Q>=minQ]
    df = df[df.H>=minH]
    df = df[df.Phyd>=minPhyd]
    QHint = interp1d(df.Q,df.H)
    QPconsint =interp1d(df.Q,df.Pcons)
    return df, QHint, QPconsint

def dP (dosya, groupby = "Q", minQ = 0.01, minH = 0.01, minPhyd = 0.01):
    df = pd.read_excel("differential_pressure/"+dosya,index_col=0)
    df = df.rename(columns={"Flow_Rate":"Q","Valve_Aperture":"D","Head":"H","Hydraulic_Power":"Phyd", \
                       "Suction_Pressure":"P1","Discharge_Pressure":"P2","Active_Power":"Pcons"})
    df = df.groupby(groupby,as_index=False).mean()
    df = df[df.Q>=minQ]
    df = df[df.H>=minH]
    df = df[df.Phyd>=minPhyd]
    QHint = interp1d(df.Q,df.H)
    QPconsint =interp1d(df.Q,df.Pcons)
    return df, QHint, QPconsint

def PompaOlcumleri (df,dfk,azami_QHint,dP_QHint,azami_QPconsint,dP_QPconsint,aralik):

    fig, ax=plt.subplots(2,1,sharex=True)
    fig.set_size_inches(8,8)
    plt.tight_layout()
    
    ax[0].scatter(df.Q,df.H,color="violet",s=15)
    ax[0].plot(df.Q,azami_QHint(df.Q),color="black")
    ax[0].set_title("Pompa Ölçümleri")
    ax[0].set_ylabel("Basma Yüksekliği (H) [m]")
    ax[0].set_ylim(bottom=0)
    ax[0].set_xlim(left=0)
    ax[0].grid()
    
    ax[0].scatter(dfk.Q,dfk.H,color="orange",s=15)
    ax[0].plot(dfk.Q,dP_QHint(dfk.Q),color="red")  
     
    ax[0].scatter(aralik[0],azami_QHint(aralik[0]),color="r",marker="|",s=700)
    ax[0].scatter(aralik[1],azami_QHint(aralik[1]),color="r",marker="|",s=700)
    
    ax[0].legend(["Sabit Eğri İnterpolasyon","Değişken Basınç İnterpolasyon","Sabit Eğri Ölçüm","Değişken Basınç Ölçüm","Eğri Uydurma Aralığı"])                                      
    
    ax[1].scatter(df.Q,df.Pcons,color="violet",s=15)
    ax[1].plot(df.Q,azami_QPconsint(df.Q),color="black")
    ax[1].set_ylabel("Güç Tüketimi (Pcons) [W]")
    ax[1].set_xlabel("Debi (Q) [m³/h]")
    ax[1].set_ylim(bottom=0)
    ax[1].set_xlim(left=0)
    ax[1].grid()
    
    ax[1].scatter(dfk.Q,dfk.Pcons,color="orange",s=15)
    ax[1].plot(dfk.Q,dP_QPconsint(dfk.Q),color="red")
    return fig

def PolyVerim (df,Q_100,H_100):
    fig, ax=plt.subplots(1,2)
    fig.set_size_inches(10,4)
    plt.tight_layout()
    
    ax[0].set_label("Q")
    ax[0].set_label("Phyd")
    ax[0].grid()
    ax[0].set_xlabel("Q")
    ax[0].set_ylabel("Phyd")
    
    ax[0].scatter(df.Q,df.Phyd,color="orange",s=5)
    ax[0].plot(df.Q,df.Phfit)
    
    ax[0].legend("Ölçüm","Phyd(Hfit)")
    
    ax[1].set_xlabel("Q")
    ax[1].set_ylabel("H")
    ax[1].plot(df.Q,df.H)
    ax[1].scatter(Q_100,H_100,color="orange")
    ax[1].annotate(" Q_100: %.2f,"%Q_100,(Q_100,H_100))
    ax[1].annotate("                      H_100: %.2f"%H_100,(Q_100,H_100))
    ax[1].grid()
    axe = ax[1].twinx()

    df["eta"] = df.Phfit/df.Pcons*100
    axe.plot(df.Q,df.eta,"violet")
    axe.set_ylim(top=100)
    axe.set_ylabel("%eta")
    axe.scatter(df.Q[df.eta.idxmax()],df.eta.max(),color="red")
    axe.annotate("%% %.2f"%df.eta.max(),(df.Q[df.eta.idxmax()],df.eta.max()))
    return fig

def duzeltilmisQH (df,Hfit,Q_100,H_100,Phydr):
    fig, ax=plt.subplots(2,1,sharex=True)
    fig.set_size_inches(8,8)
    plt.tight_layout()
    
    ax[0].plot(df.Q,Hfit(df.Q))
    
    ax[0].scatter(Q_100,H_100,color="r")
    
    ax[0].legend(["Hfit","Phydr (Q_100,H_100)"])
    ax[0].set_title("Düzeltilmiş QH Eğrisi")
    ax[0].set_ylabel("Basma Yüksekliği (H) [m]")
    ax[0].set_ylim(bottom=0)
    ax[0].set_xlim(left=0)
    ax[0].grid()
    
    ax[1].plot(df.Q,df.Phfit)
    ax[1].scatter(df.Q[df.Phfit.idxmax()],df.Phfit.max(),color="red")
    ax[1].set_ylabel("Hidrolik Güç (Phyd) [W]")
    ax[1].legend(["Phyd","Phydr (Q_100,H_100)"])
    ax[1].set_xlabel("Debi (Q) [m³/h]")
    ax[1].set_ylim(bottom=0)
    ax[1].set_xlim(left=0)
    ax[1].grid()
    
    ax[0].plot(np.full(10,Q_100),np.linspace(0,H_100,10),linestyle="-.",color="orange")
    ax[0].plot(np.linspace(0,Q_100,10),np.full(10,H_100),linestyle="-.",color="orange")
    ax[1].plot(np.full(10,Q_100),np.linspace(0,Phydr,10),linestyle="-.",color="orange")
    return fig

def sinif (ponpa, dpler):
    dPonpa=[]
    for i in dpler:
        if i.startswith(ponpa):
            dPonpa.append(i)
    return dPonpa
