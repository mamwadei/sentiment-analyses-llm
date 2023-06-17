from tweety.bot import Twitter
import re
import streamlit as st
from datetime import datetime
import os
from sentiment_analyzer import create_dataframe_from_tweets, analyze_sentiment
from typing import List,Dict
import random
import time
import plotly.graph_objects as go
import pandas as pd


def on_add_author():
    try:
        twitter_handle = st.session_state.twitter_handle
        if twitter_handle == "":
            st.session_state.error_message= "username is required"
            return
        if twitter_handle.startswith("@"):
            twitter_handle = twitter_handle[1:]
        if twitter_handle in st.session_state.twitter_handles:
            return
        tweets_details=[]
        all_tweets = twitter_client.get_tweets(twitter_handle)
        if len(all_tweets) ==0:
            return
        time.sleep(random.randint(2,2))
        for i, tweet in enumerate(all_tweets):
            tweet_detail = twitter_client.tweet_detail(tweet.id)
            if len(tweet_detail.comments) == 0:
                continue
            tweets_details.append(tweet_detail)
            if i == 5:
                break
            time.sleep(random.randint(2,3))
            
        st.session_state.twitter_handles[twitter_handle] = all_tweets[0].author.name
        st.session_state.tweets.extend(tweets_details)
        st.session_state.author_sentiment[twitter_handle] = analyze_sentiment(twitter_handle,st.session_state.tweets)
        # st.write(st.session_state.author_sentiment[twitter_handle])
    except Exception as e:
        st.session_state.error_message = e
    
    
twitter_client = Twitter()

st.set_page_config(
    layout="wide",
    page_title="SociAllytics"
)

st.title("Social Analyzer")


if not "tweets" in st.session_state:
    st.session_state.tweets = []
    st.session_state.api_key = ""
    st.session_state.twitter_handles ={}
    st.session_state.author_sentiment = {}
    st.session_state.error_message = ''

if st.session_state.error_message:
    st.error(st.session_state.error_message)

#this  is only for hakathon an then will be deleted 
st.session_state.api_key  = "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"
os.environ["OPENAI_API_KEY"]= st.session_state.api_key
    
col1, col2 = st.columns(2)

with col1:
    st.text_input("OpenAi API key", type="password", key="api_key", placeholder="sk-.......4567",
                  help="Get your API key : https://platform.openai.com/account/api-keys")
    with st.form(key="twitter_handle_form",clear_on_submit=True):
        st.subheader("Add Twitter Account", anchor=False)
        st.text_input("Analyze", key="twitter_handle" , placeholder="@twitter_username")
        submit = st.form_submit_button(label="Add Tweets",on_click=on_add_author)
    if st.session_state.twitter_handles:
        st.subheader("Twitter Accounts",anchor=False)
        for handle,name in st.session_state.twitter_handles.items():
            handle = "@" + handle
            st.markdown(f"{name}([{handle}](https://twitter.com/{handle}))")
    st.subheader("Tweets", anchor=False)
    st.dataframe(create_dataframe_from_tweets(st.session_state.tweets))
    

labels=["negative","natural","positive"] 
with col2:
    for handle,name in st.session_state.twitter_handles.items():
        author_sentiment=st.session_state.author_sentiment[handle]
        values= [author_sentiment["negative"],author_sentiment["natural"],author_sentiment["positive"]]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
        fig.update_layout(
            title=f'{name} sentiment chart',
            title_font_size= 24,
            title_x=0.2,
            legend_bgcolor="black",
            legend_font_color="white",
            legend_font_size=18,
            colorway=["yellow","green","red"]
        )
        st.plotly_chart(fig, use_container_width=True)
  