
from tweety.types import Tweet
import pandas as pd
from typing import List, Dict
from langchain.chat_models import ChatOpenAI
from langchain.chains import  LLMChain
from langchain.prompts import  PromptTemplate
import json
import re
from datetime import datetime
import time
import streamlit as st 



PROMPT_TEMPLATE ="""
Please act as a machine learning model trained for perform a supervised learning task, 
for extract the sentiment of a twitter tweets comments or replies.

You're given tweet comments or replies for this tweet "{tweet_text}":

{comments} 

Tell how positive, natural or negative the comments for that tweet. Use number between 0 and 100, where 0 to 40 negative, 41 to 59 natural and 60 tp 100 is positive for each comment and then provide the count of each category
Use a JSON using the format: 

"negative": negative count
"natural": natural count
"positive": positive count


Return just the JSON. Do not explain.

"""



def clean_tweet(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www.\S+", "", text)
    text = re.sub("([@][A-Za-z0-9_]+)|(\w+:\/\/\S+)","", text)
    return re.sub(r"\s+", " ", text)


def create_dataframe_from_tweets(tweets: List[Tweet]) -> pd.DataFrame:
    try:
        rows = []
        comments=[]
        for tweet in tweets:
            clean_text = clean_tweet(tweet.text)
            if len(clean_text) == 0:
                continue
            for comment in tweet.comments:
                comments.append({
                    "id": comment.id,
                    "text": comment.text,
                    "author": comment.author.username,
                    "date": str(comment.date.date()),
                    "views": comment.views,
                    "created_at": comment.date,
                }
                )
            rows.append({
                "id": tweet.id,
                "text": clean_text,
                "author": tweet.author.username,
                "date": str(tweet.date.date()),
                "views": tweet.views,
                "created_at": tweet.date,
                "comments": comments,
            }
            )
            
            comments=[]
            
        df = pd.DataFrame(
            rows, columns=["id", "text", "author", "date", "views", "created_at","comments"]
        )
        df.set_index("id", inplace=True)
        if df.empty:
            return df
        df = df[df.created_at.dt.date > datetime.now().date() -
                pd.to_timedelta("7Day")]
        return df.sort_values(by="created_at", ascending=False)
    except Exception as e:
        st.session_state.error_message = e

def create_list_for_prompt( tweets:List[Tweet],twitter_handle: str):
    try:
        df = create_dataframe_from_tweets(tweets)
        user_tweets= df[df.author == twitter_handle]
        if user_tweets.empty:
            return ""
        if len(user_tweets) > 100:
            user_tweets = user_tweets.sample(n=100)
        tweets_with_comments = []
        for tweet in tweets :
            text =""
            for i, comment in enumerate(tweet.comments):
                clean_comment = clean_tweet(comment.text)
                if len(clean_comment) == 0:
                    continue
                text += f"\n{i+1} - {clean_comment}"
            tweets_with_comments.append(
                {
                    "tweet_text": clean_tweet(tweet.text),
                    "comments": text
                }
            
        )
        
        return tweets_with_comments
    except Exception as e:
        st.session_state.error_message = e


def analyze_sentiment(twitter_handle:str, tweets: List[Tweet]) -> Dict[str,int]:
    try:
        full_tweets = create_list_for_prompt(tweets=tweets, twitter_handle= twitter_handle)
        chat_gpt = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        prompt = PromptTemplate(input_variables=["tweet_text","comments"],template = PROMPT_TEMPLATE)
        sentiment_chain =LLMChain(llm=chat_gpt,prompt=prompt)
        user_sentiment = {
            "negative":0,
            "natural":0,
            "positive":0,
        }
        for tweet in full_tweets:
            response = sentiment_chain(
                {
                    "tweet_text":tweet["tweet_text"],
                    "comments":tweet["comments"]
                }
            )
            res= json.loads(response["text"])
        
            user_sentiment["negative"] += user_sentiment["negative"] + res["negative"]
            user_sentiment["natural"] += user_sentiment["natural"] + res["natural"]
            user_sentiment["positive"] += user_sentiment["positive"] + res["positive"]
            time.sleep(2)

        return user_sentiment
    except Exception as e:
        st.session_state.error_message = e
    