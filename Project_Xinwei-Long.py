#############################################################web scraping###############################################
##scrap links for all sub-industries within finance market
import bs4
import urllib.request as ur
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import operator

#define the url address for each page of job posters, each page contains 100 job posters
list_of_url = []
for i in range(0,551):
    url = 'https://www.cpjobs.com/hk/SearchJobs/1?rp=1#industry=1,36,6,9,60,15,21,32,48,39&page={}'.format(i)
    list_of_url.append(url)

#abstract link of each poster
list_of_poster_links=[]
for i in range(0, len(list_of_url)):
    page = ur.urlopen(list_of_url[i]).read().decode()
    soup = bs4.BeautifulSoup(page, 'html.parser')
    post_link = soup.find_all('label', attrs={'class' : 'job_title'})
    for label_element in post_link:
        link = label_element.parent.find('a')['href'] #output link
        list_of_poster_links.append(link)

#create dataframe to store job tags and responsibiliy and requirement
Df = pd.DataFrame(columns= [
    'Title', 'Function', 'Industry', 'Work_experience',
    'Education', 'Responsibility_and_Requirement'])

#define function to scrap variables
def extract_information_of_poster (poster):
    html = ur.urlopen(poster).read().decode()
    response = bs4.BeautifulSoup(html, 'html.parser')

    try:
        factors = response.find_all('script', attrs={'type': 'application/ld+json'})
        Responsibility_and_Requirement_list = []
        for i in factors:
            for count in range(100):
                try:
                    text = i.parent.find_all('li')[count].text
                    if 'href' not in text:
                        Responsibility_and_Requirement_list.append(text)
                except:
                    break
        Responsibility_and_Requirement = ' '.join(Responsibility_and_Requirement_list).strip()
    except:
        Responsibility_and_Requirement = ''

    try:
        tag_title = response.find_all('div', attrs={'class': 'job_title'})
        for i in tag_title:
            Title = i.parent.find('h1').text.strip()
    except:
        Title = ''

    try:
        tag_function = response.find_all('th', text='Job function')
        for i in tag_function:
            Full_Function = i.parent.find('td').text
            Function = Full_Function.split('>')[0].strip()
    except:
        Function = ''

    try:
        tag_industry = response.find_all('th', text='Industry')
        for i in tag_industry:
            Industry = i.parent.find('td').text.strip()
    except:
        Industry = ''

    try:
        tag_workexp = response.find_all('th', text='Work exp')
        for i in tag_workexp:
            Work_experience = i.parent.find('td').text.strip()
    except:
        Work_experience = ''

    try:
        tag_education  = response.find_all(text='Education')
        for i in tag_education:
            Education = i.parent.parent.find('td').text.replace('<td>','').replace('</td>','').strip()
    except:
        Education = ''

        # add job tags and responsibility_and_requirement to dataframe
    Df.loc[Df.shape[0] +1] = [Title, Function, Industry, Work_experience, Education, Responsibility_and_Requirement]
    return Df

#run funciton for each poster
for i in list_of_poster_links:
    try:
        extract_information_of_poster(i)
    except:
        print('not applicable')

#save the output file of web-scrapping
os.getcwd()
Df.to_csv('Df.csv')

###########################################analysis based on web-scrapped information###################################
#read in dataframe storing web-scrapping information
Df = pd.read_csv('Finalized_Df.csv')
Df.set_index('Function',inplace= True)
#remove duplicated rows
Df = Df.drop_duplicates(subset= 'Responsibility_and_Requirement', keep='first')

# define the function for counting frequency of strings
def count_most_frequent_n_strings (string, n):
    dic = {}
    for key in string.split(' '):
        dic[key] = dic[key] + 1 if key in dic else 1
    items = sorted(dic.items(), key=lambda d: d[1], reverse=True)
    return items[:n]

##combine strings in each colum of dataframe 'Df', and check frequency
def string_counter_of_Dataframe (col, dataframe):
    list = []
    for i in dataframe[col]:
        list.append(str(i))
    combined_string = ' '.join(list).strip()
    return combined_string

Most_common_work_exp = count_most_frequent_n_strings (string_counter_of_Dataframe ('Work_experience', Df), 10)
Most_common_education = count_most_frequent_n_strings (string_counter_of_Dataframe ('Education', Df), 10)
Most_common_require_respon = count_most_frequent_n_strings (string_counter_of_Dataframe ('Responsibility_and_Requirement', Df), 500)

##after running codes above, we find work_exp & language & education actually contained in 'Most_common_require_respon')
##define category according to the result above
Category_dic = {}

Category_dic['Knowledge'] = ['Bachelor','English','PhD','Diploma','diploma','Assocaite',
                             'associate','DSE','Mathematics,','MPhil','k-means',
                             'PCA,','Boosting','Regression,','Bayes,','SVM,','ML',
                             '(PhD','English,','design','Design']
Category_dic['Socialization&teamwork'] = ['communication','team','Team','interpersonal','Communication',
                                          'Mandarin','presentation','Cantonese','Putonghua','Management','management','Manage','managing',
                                          'relationships','communication','communication,','interpersonal','independently',
                                          'meeting','meetings','organisational','Responsible','dynamic']
Category_dic['Technical'] = ['MS','Word','Excel,','data','Computer','programming','Python,','Java,','programming,',
                            'C++','R,','data-based','systems','PC','software','digital','coding',
                            'Hardware', 'microcontroller', 'Azure,', 'Cloud,', 'DialogFlow;',
                            'Tensorflow,', 'NodeJS/AngularJS', 'Android', 'Github,', 'Algorithms', 'IT',
                            'engineering'
                                   ]
Category_dic['Problem solving'] = ['analytical','Analytical''quantitative','Quantitative','pressure',
                                   'learn,','research','Research','data','analysis','hoc','innovative','self-motivated']

#####################################################PCA################################################################
#define function to count frequency of string within a set of strings
def count_frequency (list, set_of_string):
    sum = 0
    for item in list:
        count = set_of_string.count(item)
        sum += count
    return sum

# create dataframe to store percentage of eigenvalues at the end of function
Summary_of_eig_per = pd.DataFrame(columns=list(Df.index.unique()), index= [key for key in Category_dic.keys()])

#Conduct principal component analysis for each function and summarized them in a dataframe
# create the new columns for PCA
Df['Knowledge'] = 0
Df['Socialization&teamwork'] = 0
Df['Technical'] = 0
Df['Problem solving'] = 0

#run PCA
for i in Df.index.unique():
    Df_for_each_fun = Df.loc[[i]].copy()
    row_counter = 0
    #collect frequency
    for u in Df_for_each_fun['Responsibility_and_Requirement']:
        if row_counter <= len(Df_for_each_fun):
            Df_for_each_fun.iloc[row_counter,Df_for_each_fun.columns.get_loc('Knowledge')] = count_frequency (Category_dic.get('Knowledge'), str(u))
            Df_for_each_fun.iloc[row_counter,Df_for_each_fun.columns.get_loc('Socialization&teamwork')] = count_frequency (Category_dic.get('Socialization&teamwork'),str(u))
            Df_for_each_fun.iloc[row_counter,Df_for_each_fun.columns.get_loc('Technical')] = count_frequency (Category_dic.get('Technical'),str(u))
            Df_for_each_fun.iloc[row_counter,Df_for_each_fun.columns.get_loc('Problem solving')] = count_frequency (Category_dic.get('Problem solving'), str(u))
            row_counter += 1
        else:
            break
        #generate covariance matrix and eigenvalues
        cov_matrix = Df_for_each_fun.loc[:,'Knowledge':'Problem solving'].cov().values
        try:
            eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
        except:
            eigenvalues = [0,0,0,0]
        Summary_of_eig_per.loc[:,i]= eigenvalues
Summary = Summary_of_eig_per.drop(['Logistics / Transportation','Others'], axis=1)

################################################for user input##########################################################
Dic_of_scores ={}
Dic_of_scores['Knowledge'] = []
Dic_of_scores['Socialization&teamwork'] = []
Dic_of_scores['Technical'] = []
Dic_of_scores['Problem solving'] = []

def job_matcher():
    print('Hey, welcome to job matcher, we would like to know your self-evaluation of your abilites!')
    while True:
        cmd = input('''\nPlease go through all evaluations before exiting
    1) Knowledge
    2) Socialization&teamwork
    3) Technical
    4) Problem solving
    5) Exit\n''')
        if cmd == '1':
            print('Please evaluate how capable you are of following abilities by inputting number 1 to 5, greater number means more capable')
            print('\nFor True\/False question, please input 5 as Ture and 0 as False\n')
            answer_1 = float(input('You have a bachlor degree True\False'))
            answer_2 = float(input('You have a Mphil degree True\False'))
            answer_3 = float(input('You have a Doctor degree True\False'))
            answer_4 = float(input('You are good at English'))
            answer_5 = float(input('You are good at mathmatics'))
            answer_6 = float(input('You are good at machine learning or data mining'))
            Total_scores_Knowledge = answer_1 + answer_2 + answer_3 + answer_4 + answer_5 + answer_6
            Dic_of_scores['Knowledge'] = Total_scores_Knowledge
        elif cmd == '2':
            print('\nPlease evaluate how capable you are of following abilities by inputting number 1 to 5, greater number means more capable\n')
            answer_1 = float(input('You are good at communication'))
            answer_2 = float(input('You are good at teamwork'))
            answer_3 = float(input('You are good at Mandarin and Cantonese'))
            answer_4 = float(input('You can handle interpersonal relationship'))
            answer_5 = float(input('You are good at management'))
            answer_6 = float(input('You are a good meeting organizer and deliver solid presentation'))
            Total_scores_Socialization_teamwork = answer_1 + answer_2 + answer_3 + answer_4 + answer_5 + answer_6
            Dic_of_scores['Socialization&teamwork'] = Total_scores_Socialization_teamwork
        elif cmd == '3':
            print('\nPlease evaluate how capable you are of following abilities by inputting number 1 to 5, greater number means more capable\n')
            answer_1 = float(input('You are good at series of MS software'))
            answer_2 = float(input('You are good at C++ or python or R or Java'))
            answer_3 = float(input('You are good at web-developing'))
            answer_4 = float(input('You are good at developing human-machine interaction system'))
            answer_5 = float(input('You are good at developing cloud computation platform'))
            answer_6 = float(input('You are good at visual designing'))
            Total_scores_Technical = answer_1 + answer_2 + answer_3 + answer_4 + answer_5 + answer_6
            Dic_of_scores['Technical'] = Total_scores_Technical
        elif cmd == '4':
            print('\nPlease evaluate how capable you are of following abilities by inputting number 1 to 5, greater number means more capable\n')
            answer_1 = float(input('You have a analytical mind'))
            answer_2 = float(input('You are good at quantitative thinking'))
            answer_3 = float(input('You are good at researching'))
            answer_4 = float(input('You are good at analyzing data'))
            answer_5 = float(input('You can deal with ad hoc problem and work under pressure'))
            answer_6 = float(input('You are innovative'))
            Total_scores_Problem = answer_1 + answer_2 +answer_3 + answer_4 + answer_5 +answer_6
            Dic_of_scores['Problem solving'] = Total_scores_Problem
        elif cmd == '5':
            break

def Graphing_of_function():
    while True:
        cmd = input('''\n
         1) pie chart of specified function
         2) Exit\n''')
        if cmd == "1":
            function = input('\nPlease identify full name of the function\n')
            plt.pie(x= Summary[function],
                    radius= 1,
                    wedgeprops=dict(width=0.3,edgecolor='w'),
                    colors=['red','green','blue','yellow'],
                    labels= Summary.index)
            plt.title(function)
            plt.show()
        if cmd == '2':
            break

##run job matcher
job_matcher()

#output recommended function
Rank_scores = sorted(Dic_of_scores.items(), key=operator.itemgetter(1), reverse= True)
List_of_recommend_function =[]
User_highest = Rank_scores[0][0]
User_second_highest = Rank_scores[1][0]
for column in range(0,len(Summary.columns)):
     Highest = Summary.iloc[:,column].sort_values(ascending=False).index[0]
     Second_highest = Summary.iloc[:,column].sort_values(ascending=False).index[1]
     if  (Highest == User_highest) and (Second_highest == User_second_highest):
        List_of_recommend_function.append(Summary.columns.values[column])
print(List_of_recommend_function)

#pie chart based on selected function
Graphing_of_function()

#draw pie chart show distribution of user ability
plt.pie(x=Dic_of_scores.values(),
        radius=1,
        wedgeprops=dict(width=0.3, edgecolor='w'),
        colors=['red', 'green', 'blue', 'yellow'],
        labels=Summary.index)
plt.title('Distribution of user abilities')
plt.savefig('fig_user abilities.png')
plt.show()












