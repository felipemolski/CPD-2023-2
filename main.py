#import csv
#import re
import time


class PlayerData:
    def __init__(self, id, name_short, name_long, positions, nationality, club, league, ratings=None):
        self.id = id
        self.name_short = name_short
        self.name_long = name_long
        self.positions = positions
        self.nationality = nationality
        self.club = club
        self.league = league
        self.ratings = ratings or []
        self.rating_count = len(ratings) if ratings else 0 

        if ratings:
            self.rating = sum(rating for rating, _ in ratings) / len(ratings)
        else:
            self.rating = 0.0
            
class Regex:
    def __init__(self, pattern):
        self.pattern = pattern

    def match(self, s):
        matches = []
        pos = 0
        while True:
            match = s.find(self.pattern, pos)
            if match == -1:
                break

            matches.append(match)
            pos = match + len(self.pattern)

        return matches


def finditer(pattern, s):
    matches = []
    pos = 0
    while True:
        m = pattern.match(s, pos)
        if m is None:
            break

        matches.append(m)
        pos = m.end()

    return matches


def read_csv(filename):
    with open(filename, "r") as f:
        reader = f.readlines()

    records = []
    for line in reader:
        records.append(_process_line(line))

    return iter(records)


def _process_line(line):
    
    columns = []
    
    line = line.replace("\n", "")
    
    # Separe as colunas entre aspas
    quoted_columns = line.split(',"')
    
    if len(quoted_columns) == 2:
        quoted_columns[1] = quoted_columns[1].split('",')

    if len(quoted_columns) == 2:
        quoted_columns[0] = quoted_columns[0].split(",")
        quoted_columns[1][1] = quoted_columns[1][1].split(",")
    else:
        quoted_columns = line.split(",")
    
    for item in quoted_columns:
        if isinstance(item, (list, tuple)):
            for subitem in item:
                if isinstance(subitem, (list, tuple)):
                    for thirditem in subitem:
                        columns.append(thirditem)
                else:
                    columns.append(subitem)
        else:
            columns.append(item)
    
    return columns


def build_prefix_tree(players_csv):
    prefix_tree = {}

    with open(players_csv, "r") as f:
        reader = read_csv(players_csv)
        next(reader, None)  # Skip header

        for row in reader:
            name_long = row[2]

            for i in range(len(name_long)):
                prefix = name_long[:i + 1]

                if prefix not in prefix_tree:
                    prefix_tree[prefix] = []

                prefix_tree[prefix].append(row[0])

    return prefix_tree


def build_player_data_hash(players_csv, ratings_csv, tags_csv):
    start_time_total = time.perf_counter()

    player_data_hash = {}

    # Lê o arquivo players.csv
    start_time_players = time.perf_counter()

    with open(players_csv, "r") as f:
        reader = read_csv(players_csv)
        next(reader, None)  # Skip header

        for row in reader:
            #print(f"{row}")
            if len(row) == 7:
                id, name_short, name_long, positions, nationality, club, league = row

                player_data = PlayerData(
                    id=int(id),
                    name_short=name_short,
                    name_long=name_long,
                    positions=positions.split(","),
                    nationality=nationality,
                    club=club,
                    league=league,
                )

                player_data_hash[id] = player_data

    end_time_players = time.perf_counter()
    print(f"Tempo de carregamento de players.csv: {end_time_players - start_time_players:.2f} segundos")

    # Lê o arquivo ratings.csv
    start_time_ratings = time.perf_counter()

    with open(ratings_csv, "r") as r:
        reader_r = read_csv(ratings_csv)
        next(reader_r, None)  # Skip header

        for row_r in reader_r:
            if row_r[1] == str(id):
                # Atribua os ratings ao objeto PlayerData
                player_data_hash[row_r[1]].ratings = [float(rating) for rating in row_r[2:]]
                # Calcule o rating e o rating_count
                player_data_hash[row_r[1]].rating_count = len(player_data_hash[row_r[1]].ratings)
                player_data_hash[row_r[1]].rating = sum(player_data_hash[row_r[1]].ratings) / player_data_hash[row_r[1]].rating_count 
            
    end_time_ratings = time.perf_counter()
    print(f"Tempo de carregamento de ratings.csv: {end_time_ratings - start_time_ratings:.2f} segundos")

    # Lê o arquivo tags.csv
    start_time_tags = time.perf_counter()

    with open(tags_csv, "r") as t:
        reader_t = read_csv(tags_csv)
        next(reader_t, None)  # Skip header

        for row_t in reader_t:
            if row_t[0] == str(id):
                player_data.tags = [tag for tag in row_t[1:]]

    end_time_tags = time.perf_counter()
    print(f"Tempo de carregamento de tags.csv: {end_time_tags - start_time_tags:.2f} segundos")

    total_time = time.perf_counter() - start_time_total
    print(f"Tempo de carregamento total: {total_time:.2f} segundos")

    return player_data_hash



def player_query(query, player_data_hash):
    players = []

    for id, player_data in player_data_hash.items():
        for word in player_data.name_long.split():
            if query in word:
                players.append(player_data)

    players.sort(key=lambda player: player.rating, reverse=True)

    for player in players:
        print(
            f"id,{player.id},name_short,{player.name_short},name_long,{player.name_long},positions,{player.positions},rating,{player.rating:.6f},rating_count,{player.rating_count}"
        )



def user_query(rating, player_data_hash):
    players = []

    for id, player_data in player_data_hash.items():
        for rating, _ in player_data.ratings:
            if rating == int(rating):
                players.append(player_data)

    players.sort(key=lambda player: player.rating, reverse=True)

    for player in players[:20]:
        print(
            f"id,{player.id},name_short,{player.name_short},name_long,{player.name_long},positions,{player.positions},rating,{player.rating:.6f},rating_count,{player.rating_count}"
        )


def top_query(rating, player_data_hash):
    players = []

    for id, player_data in player_data_hash.items():
        if player_data.rating >= float(rating):
            players.append(player_data)

    players.sort(key=lambda player: player.rating, reverse=True)

    for player in players:
        print(
            f"id,{player.id},name_short,{player.name_short},name_long,{player.name_long},positions,{player.positions},rating,{player.rating:.6f},rating_count,{player.rating_count}"
        )

def main():
    players_csv = "players.csv"
    ratings_csv = "rating.csv"
    tags_csv = "tags.csv"

    # Build the prefix tree
    prefix_tree = build_prefix_tree(players_csv)

    # Build the player data hash
    player_data_hash = build_player_data_hash(players_csv, ratings_csv, tags_csv)

    # Process the queries
    while True:
        query = input("Entre com uma consulta: ")

        if query == "exit":
            break

        if query.startswith("player "):
            player_query(query[7:], player_data_hash)
        elif query.startswith("rating:"):
            user_query(int(query[7:]), player_data_hash)
        elif query.startswith("top:"):
            top_query(float(query[4:]), player_data_hash)
        else:
            print("Consulta inválida")


if __name__ == "__main__":
    main()
