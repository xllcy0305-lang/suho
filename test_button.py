import streamlit as st

st.title("  按钮测试")
st.write("如果你看到这行字，说明页面加载成功")

code = st.text_input("输入激活码", max_chars=12)
st.write(f"你输入了: {code}")

if st.button("点我测试"):
    st.success("按钮生效了！")
