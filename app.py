import streamlit as st
import pandas as pd
from openai import OpenAI
from streamlit_extras.stylable_container import stylable_container
import hmac

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


if not check_password():
    st.stop()

client = OpenAI(
    api_key=st.secrets.OPENAI_API_KEY
)

df = pd.read_csv('house_df.csv')

st.title('Bill Summaries')
selected = st.selectbox('Select a House bill from 2023-24', df['Bill ID'])
selected_row_index = df[df['Bill ID'] == selected].index[0]

selected_data = df[df['Bill ID'] == selected]

st.header(selected_data['Bill ID'].values[0])

if selected_data['Summary'].values[0] == 'Not yet summarized':
    if st.button('Summarize this bill'):
        with st.spinner('Summarizing...'):
            query = f'Summarize this bill: {selected_data["Bill Text"].values[0]}'

            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                # response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that concisely summarizes bills from the WA State Legislature."},
                    {"role": "user", "content": query}
                ]
            )
            
            res = response.choices[0].message.content
            df.at[selected_row_index, 'Summary'] = res  # Set new value
            df.to_csv('house_df.csv', index=False) # Overwrite the csv with the new value
            st.toast('Saved data')

            with stylable_container(
                "codeblock",
                """
                code {
                    white-space: pre-wrap !important;
                }
                """,
            ):
                st.code(res, language='markdown')
else:
    with stylable_container(
        "codeblock",
        """
        code {
            white-space: pre-wrap !important;
        }
        """,
        ):
            st.code(selected_data['Summary'].values[0], language='markdown')

