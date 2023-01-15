import google_auth_httplib2
import httplib2
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest

st.set_page_config(
    page_title="Weekly Transaction Data Entry",
    page_icon="✍️"
)

# # Create a connection object.
# credentials = service_account.Credentials.from_service_account_info(
#     dict(st.secrets["gcp_service_account"]),
#     scopes=[
#         "https://www.googleapis.com/auth/spreadsheets",
#     ],
# )
#
# conn = connect(credentials=credentials)
#


SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1Vv9eqth-gYgCof_5puEX473BeYKnzJukDC0vrZVyFqU"

# @st.experimental_singleton()
def connect_to_gsheet():
    # Create a connection object.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[SCOPE],
    )

    # Create a new Http() object for every request
    def build_request(http, *args, **kwargs):
        new_http = google_auth_httplib2.AuthorizedHttp(
            credentials, http=httplib2.Http()
        )
        return HttpRequest(new_http, *args, **kwargs)

    authorized_http = google_auth_httplib2.AuthorizedHttp(
        credentials, http=httplib2.Http()
    )
    service = build(
        "sheets",
        "v4",
        requestBuilder=build_request,
        http=authorized_http,
    )
    gsheet_connector = service.spreadsheets()
    return gsheet_connector


def get_data(gsheet_connector) -> pd.DataFrame:
    values = (
        gsheet_connector.values()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"EUR!A:E",
        )
        .execute()
    )

    df = pd.DataFrame(values["values"])
    df.columns = df.iloc[0]
    df = df[-10:]
    return df


def add_row_to_gsheet(gsheet_connector, row) -> None:
    gsheet_connector.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"EUR!A:E",
        body=dict(values=row),
        valueInputOption="USER_ENTERED",
    ).execute()

def clear_form():
    st.session_state["code"] = ""
    # st.session_state["account"] = ""
    st.session_state["amt"] = 0
    # st.session_state["purpose"] = ""
    st.session_state["comment"] = ""

gsheet_connector = connect_to_gsheet()

clear = st.button(label='Clear fields', on_click=clear_form)
form = st.form(key="annotation")

with form:
    date = st.date_input("Date:", key="date")
    account = st.selectbox("Account:", key='account', options=('Jamie Sparkasse', 'Jamie N26', 'Aayush Sparkasse', 'Aayush DB', 'Aayush N26'))

    amt = st.number_input("Amount: (negative for exp, positiv for inc)", key='amt')

    purpose = st.selectbox("Purpose:", key='purpose', options=('Exp - Living', 'Exp - Rent', 'Exp - Phone and Internet',
                                                               'Exp - Other contracts', 'Exp - Others', 'Exp - Exchange to CNY', 'Exp - Vacation',
                                                               'Exp - Entertainment', 'Income - Salary', 'Income - Scholarship', 'Income - Others'))

    comment = st.text_area("Comment:", key='comment')

    codeword = st.text_area("Code word:", key='code')
    submitted = st.form_submit_button(label="Submit")

if submitted and codeword=='MiChiQui':
    add_row_to_gsheet(
        gsheet_connector,
        [[date.strftime("%d.%m.%Y"), account, amt, purpose, comment]],
    )
    st.success("Thanks! Your data was recorded.")
elif submitted:
    st.error("Wrong code name.")
