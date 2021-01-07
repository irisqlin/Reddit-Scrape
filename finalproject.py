import sqlite3
import praw
import os
import tweepy
import matplotlib.pyplot as plt
import numpy as np
import io


# reddit password: xqsm!dU#6cK5Ybn
# sets up reddit access
def reddit_setup():
    reddit = praw.Reddit(client_id = PERSONAL_USE_SCRIPT, \
                        client_secret = SECRET_KEY, \
                        user_agent = 'coronavirus keywords', \
                        username = 'irisqlin', \
                        password = 'xxxxxxxxxxxxxxxxxx')
    return reddit
    
#arguements: reddit information, chosen subreddit, and given post limit
#returns the post limit top posts in the chosen subreddit 
def subreddit_posts(reddit, subreddit, post_limit):
    subreddit = reddit.subreddit(subreddit)
    subreddit_posts = subreddit.top(limit = post_limit)
    return subreddit_posts

#sets up to open and write to database
def setUpDatabase(db):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + '/' + db)
    cur = conn.cursor()
    return cur, conn

# arguements: reddit posts
# modifies: created a dictionary of words taken from posts the sorts based on the words
#           occurence
# returns: the sorted dictionary of
def post_to_sorted_dict(posts):
    word_dict_ALL = {}
    for submission in posts:
        text = submission.title.split()
        for word in text:
            word = word.lower().replace('.', '').replace(',', '')
            word_dict_ALL[word] = word_dict_ALL.get(word, 0) + 1
    
    word_dict_less = remove_small_words(word_dict_ALL)

    sorted_dict = sorted(word_dict_less.items(), key = lambda x: x[1], reverse=True)
    return dict(sorted_dict)

# arguments: dictionary of word and their occurrences
# modifies: sets the occurrence of the 'small words' to zero 
#           so that they are not counted in later uses
# returns: returns the modified dictionary
def remove_small_words(word_dict):
    copy = dict(word_dict)
    small_words = ['to', 'and', 'of', 'a', 'in', 'for', 'the', 'is', 'from', \
                        'are', 'on', 'he', 'that', 'not', 'will', 'with', 'be',\
                            'has', 'as', 'was', 'or', 'i', 'their', 'you', 'an', 'my', \
                                'them', 'because', 'if', 'do', 'but', '&', '-', 'your', 'it',\
                                    'this', 'by', 'have', 'at']
    for word in copy:
        for sword in small_words:
            if word == sword:
                copy[word] = 0
    return copy

# arguments: word dictionary of sorted words by occurrence, cursor and connector of database used
# requires: word dictionary needs to be over 100 words long
# modifies: checks if dictionary table for dictionary is already in existence, 
#           if table exists and number of rows less than 80, another 20 words is taken from dictionary and added
#           else table is created and first twenty words are taken from dictionary and inserted
# returns: none
def set_up_dict_db(top_hundred, cur, conn):

    cur.execute('SELECT name FROM sqlite_master WHERE type="table" and name="Reddit"')

    if len(cur.fetchall()) > 0:
        print('table already exists')
        cur.execute('SELECT count(word) FROM Reddit')
        current_len = cur.fetchone()[0]
        if current_len <= 100:
            print('current word num in Reddit table: ' + str(current_len))
            for word in get_twenty(top_hundred, current_len):
                cur.execute("INSERT OR REPLACE INTO Reddit (word, occurrence) VALUES (?,?)", (word, top_hundred[word]))
            print('additional words inserted')
        else:
            print('reddit max insertion reached')
    else:
        cur.execute("DROP TABLE IF EXISTS Reddit")
        cur.execute("CREATE TABLE Reddit (word TEXT PRIMARY KEY, occurrence INTEGER)")
        for word in get_twenty(top_hundred, 0):
            cur.execute("INSERT INTO Reddit (word, occurrence) VALUES (?,?)", (word, top_hundred[word]))
        print('Reddit table created, first 20 words inserted')
    
    conn.commit()

# arguments: sorted dictionary of words and their occurrences
# modifies: picks out top 100 items from sorted dictionary
# returns: a dictionary of top 100 words
def top_hundred(sorted_dict):
    return (dict(list(sorted_dict.items())[0: 100]))

# arguments: sorted dictionary, startings position to pick 20 words from
# modifies: picks out twenty words after start position
# returns: dictionary of twenty words to be inserted into database
def get_twenty(sorted_dict, start_pos):
    return (dict(list(sorted_dict.items())[start_pos: (start_pos + 20)]))

#arguments: sorted dictionary of words and their occurences
#modifies: none
#returns: the average length of words in the specific dictionary
def average_length_of_words(word_dict):
    num_of_words = len(word_dict)
    length_sum = 0
    for word in word_dict:
        length_sum = length_sum + len(word)
    return length_sum/num_of_words


#arguments: reddit dictionary sorted by most common occurence
#modifies: none
#returns: A graph showing the top ten words in the dictionary and their occurences
def reddit_plots(word_dict):
    tempDict = {}
    count = 0
    for i in word_dict:
        if (count < 10):
            tempDict[i] = word_dict[i]
            count = count + 1


    key1 = tempDict.keys()
    value1 = tempDict.values()
    
    plt.bar(key1,value1, color=(0.4, 0.4, 0.6, 0.6), edgecolor='gray')
    plt.xlabel("Top 10 Common Words")
    plt.ylabel("Top 10 Common Word Frequency")
    plt.title("How often do these words appear in coronavirus related reddit posts?")
    plt.show()


def main(): 

    word_dict = {}
    cur, conn = setUpDatabase('word_data.db')
    
    reddit_ = reddit_setup()
    keyword_list = ['Coronavirus', 'COVID19', 'CoronavirusUS', 'worldnews', 'CoronavirusCA']
    all_posts = []

    for key in keyword_list:
        posts = subreddit_posts(reddit_, key, 100)
        for post in posts:
            all_posts.append(post)

    #sorted dictionary made, gets top 100 words for
    word_dict = post_to_sorted_dict(all_posts)
    top_ = top_hundred(word_dict)

    #data insertion for reddit and twitter
    set_up_dict_db(top_, cur, conn)

    cur.execute('SELECT name FROM sqlite_master WHERE type="table" and name="Reddit"')
    cur.execute('SELECT count(word) FROM Reddit')
    reddit_count = cur.fetchone()[0]

    if (reddit_count >= 100):
        get_avg_join_table(cur, conn)

        reddit_plots(top_)
    
    conn.close()

  
if __name__ == "__main__":
    main()