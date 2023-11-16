#!/usr/bin/env python
# coding: utf-8

# In[1]:


from datetime import datetime

import googleapiclient.discovery
import pandas as pd
import seaborn as sns

# In[2]:


YT_API_KEY = ""  # fill in your own API key
channel_ids = [
    "UCwu4cYxN24_2O0X9ykap8hw",  # wyeth
    "UC4adGM7Q1oiH0eWYdtM_EHw",  # pediasure
    "UCx4BmO2RjaFfUv4HB685vDA",  # nutrilon
    "UC3zUFRtowBsPAEwdO6TV2bw",  # morinaga
    "UC1ucIleAU9-NWaxh2k9ltPw",  # bebelac
    "UCwU1sjdXRELEDf058SJQjhQ",  # sgm
    "UCfL8ndP9r55-K1fUnz2bAtQ",  # enfagrow
    "UC658JebjTsQJGp3GcJXZCMQ",  # lactogrow
]
yt = googleapiclient.discovery.build("youtube", "v3", developerKey=YT_API_KEY)
print(yt)


# In[3]:


def datetime_formatter(date_obj):
    # Convert to datetime object
    dt_object = datetime.strptime(date_obj, "%Y-%m-%dT%H:%M:%SZ")

    # Convert to the desired format (Month, Year)
    formatted_date = dt_object.strftime("%B, %Y")

    return formatted_date


# In[4]:


def get_channel_details(yt: any, channel_ids: list):
    request = yt.channels().list(
        part="snippet,contentDetails,statistics", id=",".join(channel_ids)
    )
    response = request.execute()
    channel_stats = [
        {
            "name": channel["snippet"]["title"],
            "published_at": datetime_formatter(channel["snippet"]["publishedAt"]),
            "views": channel["statistics"]["viewCount"],
            "subscribers": channel["statistics"]["subscriberCount"],
            "total_videos": channel["statistics"]["videoCount"],
            "upload_id": channel["contentDetails"]["relatedPlaylists"]["uploads"],
        }
        for channel in response["items"]
    ]
    return channel_stats


# In[5]:


channel_stats_data = get_channel_details(yt, channel_ids)


# In[6]:


channel_data = pd.DataFrame(channel_stats_data)


# In[7]:


channel_data


# In[8]:


channel_data["views"] = pd.to_numeric(channel_data["views"])
channel_data["subscribers"] = pd.to_numeric(channel_data["subscribers"])
channel_data["total_videos"] = pd.to_numeric(channel_data["total_videos"])
channel_data.dtypes


# ## Vs Views

# In[9]:


sns.set(rc={"figure.figsize": (20, 10)})
vc = sns.barplot(x="name", y="views", data=channel_data)


# ## Vs Subscribers

# In[10]:


sc = sns.barplot(x="name", y="subscribers", data=channel_data)


# ## Vs Total Videos

# In[11]:


sc = sns.barplot(x="name", y="total_videos", data=channel_data)


# ## Get list of video ids

# In[12]:


def get_video_ids(yt, upload_id: str):
    request = yt.playlistItems().list(
        part="contentDetails", playlistId=upload_id, maxResults=50
    )

    response = request.execute()
    vids = response["items"]
    video_ids = [vid["contentDetails"]["videoId"] for vid in vids]

    next_page = response.get("nextPageToken")
    is_next_page = True
    while is_next_page:
        if next_page is None:
            is_next_page = False
        else:
            request = yt.playlistItems().list(
                part="contentDetails",
                playlistId=upload_id,
                maxResults=50,
                pageToken=next_page,
            )
            response = request.execute()
            vids = response["items"]
            for vid in vids:
                video_ids.append(vid["contentDetails"]["videoId"])
            next_page = response.get("nextPageToken")

    return video_ids


# In[13]:


all_video_ids = []
for ch in channel_stats_data:
    all_video_ids += get_video_ids(yt, ch["upload_id"])

len(all_video_ids)


# ## Get video details

# In[14]:


def get_video_details(yt, video_ids: list):
    all_video_details = []
    for idx in range(0, len(video_ids), 50):
        request = yt.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids[idx : idx + 50]),
            maxResults=50,
        )
        response = request.execute()
        vids_details = response["items"]
        for vid in vids_details:
            all_video_details.append(
                {
                    "brand_name": vid["snippet"]["channelTitle"],
                    "title": vid["snippet"]["title"],
                    "published_date": vid["snippet"].get("publishedAt", ""),
                    "description": vid["snippet"].get("description", ""),
                    "views": vid["statistics"].get("viewCount", 0),
                    "likes": vid["statistics"].get("likeCount", 0),
                    "dislikes": vid["statistics"].get("dislikeCount", 0),
                    "favorites": vid["statistics"].get("favoriteCount", 0),
                    "link": "https://www.youtube.com/watch?v={}".format(vid["id"]),
                }
            )
    return all_video_details


# In[15]:


video_data = get_video_details(yt, all_video_ids)
len(video_data)


# In[16]:


video_df = pd.DataFrame(video_data)
video_df["published_date"] = pd.to_datetime(video_df["published_date"]).dt.date
video_df["views"] = pd.to_numeric(video_df["views"])
video_df["likes"] = pd.to_numeric(video_df["likes"])
video_df["dislikes"] = pd.to_numeric(video_df["dislikes"])
video_df["favorites"] = pd.to_numeric(video_df["favorites"])
video_df.dtypes


# In[17]:


top_10_by_views = video_df.sort_values(by="views", ascending=False).head(10)


# In[18]:


top_10_by_views


# In[19]:


sns.set(rc={"figure.figsize": (10, 8)})
top_videos_chart_from_all_channels = sns.barplot(
    x="views", y="title", hue="brand_name", data=top_10_by_views
)


# In[20]:


import base64

from IPython.display import HTML


def create_download_link(df, title="Download CSV file", filename="data.csv"):
    csv = df.to_csv()
    b64 = base64.b64encode(csv.encode())
    payload = b64.decode()
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    html = html.format(payload=payload, title=title, filename=filename)
    return HTML(html)


create_download_link(video_df)


# In[ ]:
