import streamlit as st

st.set_page_config(page_title="AtlasTrade", layout="wide")

st.title("📈 AtlasTrade - Hisse Analiz Demo")

st.markdown("""
Bu demo, THYAO (Türk Hava Yolları) hissesinin örnek teknik ve temel analizine göre 
3-5 günlük kısa vadeli %5-10 kâr hedefli işlem fırsatlarını göstermek için tasarlanmıştır.
""")

st.subheader("🚧 Demo Sürüm Notu")
st.info("Bu sadece bir prototiptir. Gerçek zamanlı veri ve sinyal üretimi içermez. Amaç, kullanıcı arayüzü fikri vermektir.")

st.subheader("🔍 Teknik Analiz Örneği (Statik Verilerle)")
st.write("• RSI: 42 (Nötr)
• MACD: Sat sinyali
• Hareketli Ortalamalar: Fiyat, 20 günlük ortalamanın altında")

st.subheader("📰 Temel Analiz & Haber Başlıkları (Statik Örnek)")
st.write("• 2024 Q4 bilançosu beklentinin %10 üzerinde geldi
• CEO açıklaması: 2025’te agresif büyüme hedefi")

st.subheader("📌 Sonuç ve Öneri")
st.success("Beklenen alım noktası: 245 TL civarı
Hedef satış noktası: 260 - 270 TL
Stop loss: 239 TL")

st.caption("Geliştirici: AtlasTrade | Bu sadece bir kullanıcı arayüzü demosudur.")
