import streamlit as st
import pandas as pd
import matplotlib as mp
import matplotlib.pyplot as plt
import json
import requests
import html
import plotly.express as px

@st.cache_data
def get_api_data():
    with open('allcards.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    return data

@st.cache_data
def read_and_prepare(path):
    
    data = get_api_data()

    card_names = [card['name'] for card in data]
    card_names = sorted(list(set(card_names))) #удаляем дубликаты в данных (а они там есть!)
    card_names = [card for card in card_names if (('Rank 2' not in card) & ('Rank 3' not in card))] #эти карты нельзя использовать для создания колоды


    

    keys_str = ['regim', 'rating', 'Class', 'creation_date', 'deck_type','deck_archetype', 'code']

    keys_int = ['minion_count', 'spell_count', 'weapon_count',
                      'craft_cost']
    types1 = {key: str for key in keys_str}
    types2 = {key: int for key in keys_int}

    types3 = {name: int for name in card_names} # Ради этой строчки написаны эти два блока кода
    types = types1 | types2 | types3

    df = pd.read_csv(path, dtype = types)
    df = df[df['craft_cost'] != 0]  #удаляем колоды без карт 

    date_format = "%m/%d/%Y"
    df['creation_date'] = pd.to_datetime(df['creation_date'], format=date_format)

    df.set_index(pd.DatetimeIndex(df['creation_date']), inplace=True)  # Сделаем колонку с индексами
    df.index.names = ['Date']
    df = df[~df['deck_type'].isin(['Arena', 'PvE Adventure'])]  




    #Подготовим сведения о том, какими карты являются по редкости, и какими способностями (keywords) они обладают
    
    def get_card_rarity(card_name, cards_data):
        for card in cards_data:
            if card.get('name') == card_name:
                return card.get('rarity')
            
    def get_card_mechanics(card_name, cards_data):
        for card in cards_data:
            if card.get('name') == card_name:
                return card.get('mechanics')

    def get_card_referencedTags(card_name, cards_data):
        for card in cards_data:
            if card.get('name') == card_name:
                return card.get('referencedTags')

#Создадим соответствующие списки из карт, согласно их редкости и способностям

    rare_cards = [card for card in card_names if get_card_rarity(card, data) == 'RARE']
    epic_cards = [card for card in card_names if get_card_rarity(card, data) == 'EPIC']
    legendary_cards = [card for card in card_names if get_card_rarity(card, data) == 'LEGENDARY']

    battlecry_cards = [card for card in card_names
                    if get_card_mechanics(card, data) is not None
                    and 'BATTLECRY' in get_card_mechanics(card, data)]
    deathrattle_cards = [card for card in card_names 
                     if get_card_mechanics(card, data) is not None 
                     and 'DEATHRATTLE' in get_card_mechanics(card, data)]
    stealth_cards = [card for card in card_names 
                 if get_card_mechanics(card, data) is not None
                 and 'STEALTH' in get_card_mechanics(card, data)]
    charge_cards1 = [card for card in card_names 
                if (get_card_mechanics(card, data) is not None)
                and 'CHARGE' in (get_card_mechanics(card, data))]
    charge_cards2 = [card for card in card_names 
                if (get_card_referencedTags(card, data) is not None)
                and 'CHARGE' in (get_card_referencedTags(card, data))]

    charge_cards = sorted(list(set(charge_cards1 + charge_cards2)))

    discover_cards = [card for card in card_names 
                  if get_card_mechanics(card, data) is not None
                  and 'DISCOVER' in get_card_mechanics(card, data)]
    rush_cards = [card for card in card_names 
              if get_card_mechanics(card, data) is not None
              and 'RUSH' in get_card_mechanics(card, data)]
    taunt_cards = [card for card in card_names 
               if get_card_mechanics(card, data) is not None
               and 'TAUNT' in get_card_mechanics(card, data)]

    properties_rarity = {'rare_cards' : rare_cards, 'epic_cards': epic_cards, 'legendary_cards': legendary_cards}

    properties_type = {'battlecry_cards': battlecry_cards,
             'deathrattle_cards': deathrattle_cards, 'stealth_cards': stealth_cards, 'charge_cards': charge_cards, 'discover_cards': discover_cards,
             'rush_cards': rush_cards, 'taunt_cards': taunt_cards}
    for column in properties_type:
        df[column] = df[properties_type[column]].sum(axis=1)
    for column in properties_rarity:
        df[column] = df[properties_rarity[column]].sum(axis=1)
    
    df['common_and_class_cards'] = 30 - df['rare_cards'] - df['epic_cards'] - df['legendary_cards']

    return df

df = read_and_prepare('DataTable.csv')

st.title('Мы работаем со следующим датасетом: данные о пользовательских колодах, загруженные на сайт Hearthpnw и предназначенные для соревновательного режима Ranked  с информацией о содержащихся в них картах.')
         

st.markdown('**Давайте посмотрим на некоторые визуализации наших данных:**')
st.write('Имеем следующую разбивку по популярности классов:')
Set3 = [(141,211,199), (255,255,179), (190,186,218), (251,128,114), (128,177,211),
        (253,180,98), (179,222,105), (252,205,229), (217,217,217), (188,128,189), (204,235,197), (255,237,111)] # ну красиво же?)


def rgb_to_hex(rgb):
    r, g, b = rgb
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

Classes_counts = df['Class'].value_counts()
fig = plt.figure(figsize=(10, 2))
Classes_counts.plot.bar(color = list(map(rgb_to_hex, Set3)), edgecolor = 'black')
plt.xticks(rotation=0)
st.pyplot(fig)

st.write('А вот так распределена стоимость колод в единицах пыли (dust):')
fig, ax = plt.subplots()
df['craft_cost'].hist(bins = 100, range = (0, 15000), ax=ax)
ax.set_ylabel('Number of Decks')
ax.set_xlabel('Craft Cost')
st.pyplot(fig)


st.markdown('**Что насчет числа созданных колод на протяжении времени?**')

@st.cache_data
def get_decks_per_day(path):
    df =  read_and_prepare(path)
    decks_per_day = df.groupby(df['creation_date']).size().reset_index(name='count')
    return decks_per_day

decks_per_day = get_decks_per_day('DataTable.csv')

fig = plt.figure(figsize=(10, 5))

plt.plot(decks_per_day['creation_date'], decks_per_day['count'], marker='o', linestyle='', alpha = 0.5)
st.pyplot(fig)

st.markdown("""
И если всплеск в октябре 2013 года объясняется проводимым на сайте событием, то
все последующие являются следствием добавления новых карт или изменений баланса. Речь о
 :red[патчах] (expansions), :blue[приключениях]  (adventures) и обычных :gray[изменениях баланса].
            """)

adventures = {'Curse of Naxxramas': "22/07/2014", 'Blackrock Mountain': "02/04/2015", 'The League of Explorers': "12/11/2015"}
for key in adventures:
    adventures[key] = pd.to_datetime(adventures[key], format = "%d/%m/%Y")

expansions = {'Goblins vs Gnomes': "08/12/2014", 'The Grand Tournament': "24/08/2015", 'Whispers of the Old Gods': "26/05/2016"}
for key in expansions:
    expansions[key] = pd.to_datetime(expansions[key], format = "%d/%m/%Y")


fig = plt.figure(figsize=(10, 5))
plt.plot(decks_per_day['creation_date'], decks_per_day['count'], marker='o', linestyle='', alpha = 0.7, markersize=5)
plt.xlabel('Дата')
plt.ylabel('Количество созданных за день колод')
#plt.title('Number of Decks Created Each Day')
plt.grid(axis='y')
plt.xticks(rotation=45)

last_date_observed = df.iloc[df.shape[0] - 1, 7]


for adventure in adventures:
    if adventures[adventure] < last_date_observed:  
        plt.axvline(adventures[adventure], color = 'blue', alpha = 0.7)

for expansion in expansions:
    if expansions[expansion] < last_date_observed:  
        plt.axvline(expansions[expansion], color = 'red', alpha = 0.7)


st.pyplot(fig)

st.write('Приятно, когда причинно-следственная связь и очевидна, и отчетливо видна на данных.')

st.markdown('**Что бы еще посмотреть? Давайте взглянем на состав колод относительно типов содержащихся в них карт: существ, заклинаний и оружий.**')

last_date_observed = df.iloc[df.shape[0] - 1, 7]

@st.cache_data
def show_rarity_structure(Class, window, show_sets_flag = False):  # Окно будет соответствовать дням, а не колодам!
    columns_rarity = ['common_and_class_cards', 'rare_cards', 'epic_cards', 'legendary_cards']

    if Class == 'Все':
        grouped = df[columns_rarity].groupby(df['creation_date']).mean().rolling(window=window).mean()
        grouped = grouped.iloc[window:]
        fig = px.area(grouped, labels = {'value': 'Rarity structure', 'index': 'Creation date'}, title = 'Averaged rarity structure of all decks')
    else:
        df_class = df[df['Class'] == Class] 
        grouped = df_class[columns_rarity].groupby(df_class['creation_date']).mean().rolling(window=window).mean()
        grouped = grouped.iloc[window:]
        fig = px.area(grouped, labels = {'value': 'Rarity structure', 'index': 'Creation date'}, title = f'Rarithy structure of {Class} decks')

    if show_sets_flag:
        for adventure in adventures:
            if adventures[adventure] < last_date_observed:
                fig.add_vline(x=adventures[adventure], line_width=2, line_color = 'blue', opacity=0.4)
        for expansion in expansions:
            if expansions[expansion] < last_date_observed:
                fig.add_vline(x=expansions[expansion], line_width=2, line_color = 'red', opacity=0.4)
    st.plotly_chart(fig)

Classes = ['Mage', 'Priest', 'Warlock', 'Druid', 'Paladin', 'Hunter', 'Warrior', 'Rouge', 'Shaman']

Class = st.selectbox('Выберете класс', Classes + ['Все'])
show_sets_flag = st.checkbox('Показать приключения и патчи')
show_rarity_structure(Class, 30, show_sets_flag)

st.write('Можно видеть, как у Воина график довольно подвижный, относительно других классов.')

st.markdown('**Давайте посмотрим теперь на популярность конкретных карт:**')

def get_popularity(card):
    
    def get_card_class(card_name, cards_data):
        for card in cards_data:
            if card.get('name') == card_name:
                return card.get('cardClass').capitalize()
            
    data = get_api_data()
    card_class = get_card_class(card, data)
    
    if card_class in Classes:
        df_classed = df[df['Class'] == card_class]
        card_data = df_classed[[card, 'creation_date']]
        

        popularity = card_data.groupby(card_data['creation_date']).mean().rolling(window=20).mean()
        popularity = popularity.reset_index()

    else:
        card_data = df[[card, 'creation_date']]
        popularity = card_data.groupby(card_data['creation_date']).mean().rolling(window=20).mean()
        popularity = popularity.reset_index()


    return popularity, card_class
def show_popularity(card):
    popularity, card_class = get_popularity(card)
    fig = px.line(popularity, x='creation_date', y=card, title=f'{card} popularity over time in {card_class} decks' if card_class in Classes else f'{card} popularity over time across all decks')
    
    for adventure in adventures:
        if adventures[adventure] < last_date_observed:
            fig.add_vline(x=adventures[adventure], line_width=2, line_color = 'blue', opacity=0.4)
    for expansion in expansions:
        if expansions[expansion] < last_date_observed:
            fig.add_vline(x=expansions[expansion], line_width=2, line_color = 'red', opacity=0.4)
            
    fig.update_layout(
    xaxis_title='Date',
    yaxis_title=f'Average number in decks')
    st.plotly_chart(fig)

data = get_api_data()

card_names = [card['name'] for card in data]
card_names = sorted(list(set(card_names))) #удаляем дубликаты в данных (а они там есть!)
card_names = [card for card in card_names if (('Rank 2' not in card) & ('Rank 3' not in card))] #эти карты нельзя использовать для создания колоды


cards = st.multiselect('Выберете карты', card_names)
for card in cards:
    show_popularity(card)

st.title('The end')
