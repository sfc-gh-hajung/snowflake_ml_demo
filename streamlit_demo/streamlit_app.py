import streamlit as st
from my_package.my_functions import say_hello

def main():
    st.title("Streamlit App with Custom Package")
    message = say_hello("World")
    st.write(message)

if __name__ == "__main__":
    main()