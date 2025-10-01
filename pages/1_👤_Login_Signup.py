import streamlit as st
from utils.db import init_db, get_user_by_email, insert_user
from utils.auth import hash_password, verify_password, create_jwt, decode_jwt

st.title("👤 Login / Signup")

init_db()

mode = st.radio("Choose mode", ["Login", "Signup"], horizontal=True)

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if mode == "Signup":
    role = st.selectbox("Role", ["User", "Analyst", "Admin"])
    if st.button("Create Account"):
        if not email or not password:
            st.error("Please provide email and password.")
        else:
            ok, err = insert_user(email, hash_password(password), role)
            if ok:
                st.success("Account created. You can Login now.")
            else:
                st.error(f"Signup failed: {err}")
else:
    if st.button("Login"):
        user = get_user_by_email(email)
        if not user:
            st.error("No such user")
        else:
            if verify_password(password, user["password_hash"]):
                token = create_jwt({"sub": user["id"], "email": user["email"], "role": user["role"]})
                st.session_state["token"] = token
                st.session_state["user"] = {"id": user["id"], "email": user["email"], "role": user["role"]}
                st.success(f"Welcome {user['email']}! Use the sidebar to navigate.")
            else:
                st.error("Invalid password")

if "token" in st.session_state:
    dec = decode_jwt(st.session_state["token"])
    if dec:
        st.info(f"Logged in as **{dec.get('email')}** ({dec.get('role')})")
        if st.button("Logout"):
            for k in ["token","user"]:
                st.session_state.pop(k, None)
            st.rerun()
