import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os
from eei_lib import *

st.set_page_config(
 page_title='EEI',
 layout="wide",
 initial_sidebar_state="expanded",
)

st.sidebar.title("EEI Hesaplayıcı")
st.sidebar.markdown('''
Pompa verilerini ve eğri uydurma aralığını seçerek ölçülen değerler ve EEI hesaplarına ulaşabilirsiniz.
'''
)

###############################################################################
# sidebar
###############################################################################

st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 400px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 500px;
        margin-left: -500px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("Kontrol Paneli")
    
sbtler = sorted(os.listdir("constant_rev"))

dosya = st.sidebar.selectbox(
    "Max devirde sabit eğri",
    sbtler)

ponpa = dosya.split("_")[0]

dpler = sorted(os.listdir("differential_pressure"))

dPonpa = sinif (ponpa,dpler)

kismi = st.sidebar.selectbox(
    "Oransal Basınç Modu (dP)",
    dPonpa)


    

###############################################################################
# veri okuma & ön düzeltmeler
###############################################################################

df, azami_QHint, azami_QPconsint = azami (dosya)
dfk, dP_QHint, dP_QPconsint = dP (kismi)

aralik = st.sidebar.slider(
    "Eğri uydurma aralığını seç (Debi [Q])",
    df.Q.min(),df.Q.max(),(float(df.Q.min()),float(df.Q.max())))
aralik = np.array(aralik)

kes=df[df.Q.between(aralik[0],aralik[1])]                                       
Hfit = np.poly1d(np.polyfit(kes.Q,kes.H,3))
df["Phfit"] = df.Q*Hfit(df.Q)*2.72
Phydr = df.Phfit.max()
Q_100 = df.Q[df.Phfit.idxmax()]
H_100 = Hfit(df.Q[df.Phfit.idxmax()])

dfk = dfk[dfk.Q<=Q_100*1.3]                                            
dfk = dfk[dfk.Q>=Q_100/6]


###############################################################################
# ham veri grafikleri
###############################################################################

konteyner_1 = st.container()
kols_1 = konteyner_1.columns([1,1])

fig = PompaOlcumleri (df,dfk,azami_QHint,dP_QHint,azami_QPconsint,dP_QPconsint,aralik)
kols_1[0].pyplot(fig)

kols_1[1].markdown("""* Pompa Ölçümleri test düzeneğinde yapıldı.
* Ölçümler 3. derece eğriye uyduruldu.
""")

kols_1[1].write("** Q_max      :%.2f m³/h **" %(df.Q.max()))
kols_1[1].write("** H_max      :%.2f m **" %(df.H.max()))
kols_1[1].write("** Pcons_max  :%.2f W **" %(df.Pcons.max()))
kols_1[1].write("** Phyd_max  :%.2f W **" %(df.Phyd.max()))


with konteyner_1.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_1.png")
    
with konteyner_1.expander("Polyfit Yardımcısı & Verim (%eta)"):
    fig = PolyVerim(df, Q_100, H_100)
    st.pyplot(fig)


###############################################################################
# Hfit
###############################################################################

konteyner_2 = st.container()
kols_2 = konteyner_2.columns([1,1])                                                                

fig = duzeltilmisQH(df, Hfit, Q_100, H_100, Phydr)
kols_2[0].pyplot(fig)


kols_2[1].markdown("""* Hfit üzerinde hidrolik gücün en yüksek olduğu nokta (P_hydr) hesaplandı.
* P_hydr'a karşılık gelen debi (Q_100) bulundu.'
* Hfit eğrisi üzerinde Q_100 değerinin çıktısı H_100 hesaplandı.
""")

kols_2[1].write("** P_hydr      :%.2f W **" %(Phydr))
kols_2[1].write("** Q_100       :%.2f m³/h **" %(Q_100))
kols_2[1].write("** H_100       :%.2f m **" %(H_100))

with konteyner_2.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_2.png")
    
###############################################################################
# Tolerans hesabı
###############################################################################

konteyner_4 = st.container()
kols_4 = konteyner_4.columns([1,1])

yuzde = (H_100)-(H_100*0.2)
eksi = (H_100)-0.5
H_100tol = np.array([yuzde,eksi]).max()
t = H_100tol-H_100

fig, ax=plt.subplots(1,1,sharex=True)
fig.set_size_inches(8,4)
plt.tight_layout()

ax.plot(df.Q,Hfit(df.Q))
ax.scatter(Q_100,H_100,color="red")
ax.scatter(Q_100,H_100tol,color="orange")
ax.arrow(Q_100,H_100,0,t,length_includes_head=True,head_width=0.04)
ax.annotate("   H_100: %.2f"%H_100,(Q_100,H_100))
ax.annotate("   H_100t: %.2f"%H_100tol,(Q_100,H_100tol))
ax.set_ylim(bottom=H_100*0.7,top=H_100*1.3)
ax.set_xlim(left=Q_100*0.7,right=Q_100*1.3)
ax.set_title("Azami Hidrolik GÜçte H_100 Toleransı")
ax.set_ylabel("Basma Yüksekliği (H) [m]")
ax.set_xlabel("Debi (Q) [m³/h]")
kols_4[0].pyplot(fig)

kols_4[1].write("H_100 - H_100*0.20 = %.2f" %yuzde)
kols_4[1].write("H_100 - 0.5m = %.2f" %eksi)
kols_4[1].write(" * H_100 toleransı hesaplandı.")
kols_4[1].write("   * ** H_100t = %.2f **"%H_100tol)

if kols_4[1].button("Toleranslı H_100 ile hesap yap"):
    H_100 = H_100tol

with konteyner_4.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_4.png")


###############################################################################
# Pref
###############################################################################

konteyner_3 = st.container()
kols_3 = konteyner_3.columns([1,1])

Pref=1.7*Phydr+17*(1-np.e**(-0.3*Phydr))

kols_3[0].write("** P_ref = %.2f **" %Pref)
kols_3[1].write(" * Referans Güç (P_ref) hesaplandı.")

with konteyner_3.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_3.png")
    
###############################################################################
# Referans kontrol eğrisi
###############################################################################

konteyner_5 = st.container()
kols_5 = konteyner_5.columns([4,1,1,1,1])

Qrefl=np.linspace(0,Q_100,5)
Hrefl=np.linspace(H_100*0.5,H_100,5)
Qref=Qrefl[1:]
Href=Hrefl[1:]

fig, ax=plt.subplots(1,1)
fig.set_size_inches(8,4)

ax.plot(df.Q,Hfit(df.Q))
#ax.scatter(Qref,Href,color="red")
ax.errorbar(Qref,Href,xerr=Qref*0.1,fmt='o')
ax.plot(Qrefl,Hrefl,color="violet")
ax.set_title("Referans Kontrol Eğrisi")
ax.scatter(dfk.Q,dfk.H,color="green",s=3)
#ax.plot(dfk.Q,dP_QHint(dfk.Q))

ax.set_ylabel("Basma Yüksekliği (H) [m]")
ax.set_xlabel("Debi (Q) [m³/h]")
ax.set_ylim(bottom=0)
ax.set_xlim(left=0)
ax.grid()
ax.legend(["Hfit","Ref.Kontrol Eğrisi","dP Ölçümleri","Pref %10 tolerans"])

kols_5[0].pyplot(fig)

kols_5[1].subheader("Q_25ref")
kols_5[1].write("Q_25=%.2f"%Qref[0])
kols_5[1].write("H_25=%.2f"%Href[0])
kols_5[1].write("Ölçümler %10 tolerans değerinin içerisinde kaldığı için interpolasyon yapılır.")

kols_5[2].subheader("Q_50ref")
kols_5[2].write("Q_50=%.2f"%Qref[1])
kols_5[2].write("H_50=%.2f"%Href[1])

kols_5[3].subheader("Q_75ref")
kols_5[3].write("Q_75=%.2f"%Qref[2])
kols_5[3].write("H_75=%.2f"%Href[2])

kols_5[4].subheader("Q_100ref")
kols_5[4].write("Q_100=%.2f"%Qref[3])
kols_5[4].write("H_100=%.2f"%Href[3])



with konteyner_5.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_5.png")
    

###############################################################################
# Ölçüm düzeltme sidebar
###############################################################################

kontey = st.container()
kolsey = st.sidebar.columns([1,1])
Qm=np.zeros(4)
Hm=np.zeros(4)
Pm=np.zeros(4)

st.sidebar.title("Ölçüm Düzeltme")
st.sidebar.subheader("Q_25 Ölçümleri")
Qm[0] = st.sidebar.number_input("Q_25",value=Qref[0])
Hm[0] = st.sidebar.number_input("H_25",value=np.round(dP_QHint(Qref[0]),2))
Pm[0] = st.sidebar.number_input("P_25",value=np.round(dP_QPconsint(Qref[0]),2))

st.sidebar.subheader("Q_50 Ölçümleri")
Qm[1] = st.sidebar.number_input("Q_50",value=Qref[1])
Hm[1] = st.sidebar.number_input("H_50",value=np.round(dP_QHint(Qref[1]),2))
Pm[1] = st.sidebar.number_input("P_50",value=np.round(dP_QPconsint(Qref[1]),2))

st.sidebar.subheader("Q_75 Ölçümleri")
Qm[2] = st.sidebar.number_input("Q_75",value=Qref[2])
Hm[2] = st.sidebar.number_input("H_75",value=np.round(dP_QHint(Qref[2]),2))
Pm[2] = st.sidebar.number_input("P_75",value=np.round(dP_QPconsint(Qref[2]),2))

st.sidebar.subheader("Q_100 Ölçümleri")
Qm[3] = st.sidebar.number_input("Q_100",value=Qref[3])
Hm[3] = st.sidebar.number_input("H_100",value=np.round(dP_QHint(Qref[3]),2))
Pm[3] = st.sidebar.number_input("P_100",value=np.round(dP_QPconsint(Qref[3]),2))


###############################################################################
# Nokta ölçümleri
###############################################################################

konteyner_8 = st.container()
kols_8 = konteyner_8.columns([4,1,1,1,1])

fig, ax=plt.subplots(1,1)
fig.set_size_inches(8,4)

ax.plot(df.Q,Hfit(df.Q))
ax.scatter(Qref[0:4],Href[0:4],color="red")
ax.plot(Qrefl,Hrefl,color="violet")
ax.set_title("Oransal Basınç Modunda Ölçümler")

ax.scatter(Qm,Hm,color="black", marker="x",s=50)
ax.legend(["Hfit","Ref.Kontrol Eğrisi","Ref.Noktaları","Ölçülen Değerler"])
ax.set_ylabel("Basma Yüksekliği (H) [m]")
ax.set_xlabel("Debi (Q) [m³/h]")
ax.set_ylim(bottom=0)
ax.set_xlim(left=0)
ax.grid()

kols_8[0].pyplot(fig)

percerQ = np.abs((Qref-Qm)/Qref)*100
percerH = np.abs((Href-Hm)/Href)*100

kols_8[1].subheader("Q_25")
kols_8[1].write("Q_25=%.2f"%Qm[0])
kols_8[1].write("H_25=%.2f"%Hm[0])
kols_8[1].write("P_25=%.2f"%Pm[0])
kols_8[1].write("%% dQ_25=%.2f"%percerQ[0])
kols_8[1].write("%% dH_25=%.2f"%percerH[0])

kols_8[2].subheader("Q_50")
kols_8[2].write("Q_50=%.2f"%Qm[1])
kols_8[2].write("H_50=%.2f"%Hm[1])
kols_8[2].write("P_50=%.2f"%Pm[1])
kols_8[2].write("%% dQ_50=%.2f"%percerQ[1])
kols_8[2].write("%% dH_50=%.2f"%percerH[1])

kols_8[3].subheader("Q_75")
kols_8[3].write("Q_75=%.2f"%Qm[2])
kols_8[3].write("H_75=%.2f"%Hm[2])
kols_8[3].write("P_75=%.2f"%Pm[2])
kols_8[3].write("%% dQ_75=%.2f"%percerQ[2])
kols_8[3].write("%% dH_75=%.2f"%percerH[2])

kols_8[4].subheader("Q_100")
kols_8[4].write("Q_100=%.2f"%Qm[3])
kols_8[4].write("H_100=%.2f"%Hm[3])
kols_8[4].write("P_100=%.2f"%Pm[3])
kols_8[4].write("%% dQ_100=%.2f"%percerQ[3])
kols_8[4].write("%% dH_100=%.2f"%percerH[3])

with konteyner_8.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_8.png")

###############################################################################
# PLavg
###############################################################################

konteyner_9 = st.container()
kols_9 = konteyner_9.columns([1,1,1])

pb = Pm*(Href>= Hm)*Href/Hm
pk = Pm*(Href<Hm)
Pl = pb + pk

L=np.array([0.44,0.35,0.15,0.06])
PLavg=(Pl*L).sum()

kols_9[1].write("PLavg = %.2f" %PLavg)

with konteyner_9.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_9.png")

with konteyner_9.expander("TS EN 16297-2:2013-04 atıf"):
    st.image("fig/TSE_7.png")
    
###############################################################################
# EEI
###############################################################################

konteyner_10 = st.container()
kols_10 = konteyner_10.columns([1,1,1])

EEI = PLavg/Pref*0.49

kols_10[1].write("EEI = %.3f"%EEI)

with konteyner_10.expander("TS EN 16297-1:2013-04 atıf"):
    st.image("fig/TSE_10.png")

with konteyner_10.expander("TS EN 16297-2:2013-04 atıf"):
    st.image("fig/TSE_11.png")




