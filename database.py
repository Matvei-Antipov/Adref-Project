import random
from pymongo import MongoClient
from constants import API_KEY_MONGO

#database MongoDB

cluster = MongoClient(API_KEY_MONGO)

db = cluster['adref']
adref = db['adref']
games = db['games']
tickets = db['tickets']
tasks = db['tasks']
completed_tasks = db['completed_tasks']

#insertation when registration is going
def insert_user(user_id: str):
    account = {
            'user_id': user_id,
            'balance': 0,
            'invited_referals':  0,
            'completed_tasks': 0
        }
    adref.insert_one(account)

#find user
def find_user(user_id: str) -> bool:
    user = adref.find_one({"user_id": user_id})
    if user:
        return True
    else:
        return False

#get info
def get_info(user_id: str) -> dict:
    user_data = adref.find_one({"user_id": user_id})
    if user_data:
        return {
            "user_id": user_data.get("user_id"),
            "balance": user_data.get("balance", 0),
            "invited_referals": user_data.get("invited_referals", 0),
            "completed_tasks": user_data.get("completed_tasks", 0),
        }
    return None

#get games
def get_games(user_id: str) -> dict:
    user_data = games.find_one({"user_id": user_id})
    if user_data:
        return {
            "user_id": user_data.get("user_id"),
            "bet": user_data.get("bet", 0),
            "result_value": user_data.get("result_value", 0),
            "result_status": user_data.get("result_status", 0),
            "counter": user_data.get("counter", 0),
            "game": user_data.get("game", 0)
        }
    return False

#update balance
def update_balance(user_id: str, amount: int):
    adref.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount}}
    )

#set balance
def set_balance(user_id: int, amount: int):
    adref.update_one(
        {"user_id": user_id},
        {"$set": {"balance": amount}}
    )

#update bet
def update_game(user_id: str, amount: int, status: str):
    if status == "bet":
        games.update_one(
            {"user_id": user_id},
            {"$inc": {"bet": amount}}
        )
    if status == "predict":
        games.update_one(
            {"user_id": user_id},
            {"$set": {"result_value": amount}}
        )
    if status == "status":
        games.update_one(
                {"user_id": user_id},
                {
                    "$inc": {
                        "counter": 1,
                    },
                    "$set": {
                        "result_status": amount,
                    }
                }
        )
    if status == "game":
        games.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "game": amount,
                    }
                }
        )

#insert_game
def insert_game(game_info: dict):
    if games.insert_one(game_info):
        return True
    else:
        return False

#delete games
def delete_games(user_id: str):
    games.delete_many({"user_id": user_id})

#ticket id generator
def generate_ticket_id(username: str):
    last_ticket_cursor = tickets.find().sort("ticket_id", -1).limit(1)
    
    last_ticket_list = list(last_ticket_cursor)
    
    if len(last_ticket_list) == 0:
        new_ticket_id = 'AA0000001'
    else:
        last_ticket_id = last_ticket_list[0]['ticket_id']
        
        letters = last_ticket_id[:2]
        number = int(last_ticket_id[2:])
        
        number += 1
        
        if number > 9999999:
            letters = increase_letters(letters)
            number = 1
        
        new_ticket_id = f"{letters}{str(number).zfill(7)}"
    
    tickets.insert_one(
        {
            "ticket_id": new_ticket_id,
            "username": username, 
            "status": "opened"
        }
    )
    
    return new_ticket_id

def increase_letters(letters):
    first, second = letters
    if second == 'Z':
        second = 'A'
        if first == 'Z':
            first = 'A'
        else:
            first = chr(ord(first) + 1)
    else:
        second = chr(ord(second) + 1)
    
    return first + second

#get tickets
def get_tickets(username: str) -> dict:
    user_data = tickets.find_one({"user_id": username})
    if user_data:
        return {
            "ticket_id": user_data.get("ticket_id"),
            "username": user_data.get("username", 0),
            "status": user_data.get("status", 0)
        }
    return False

#delete ticket
def delete_ticket(ticket_id: str):
    tickets.delete_one({"ticket_id": ticket_id})

#count tasks
def count_tasks() -> int:
    total_count = tasks.count_documents({})
    return total_count

#add task
def add_task(name: str) -> int:
     while True:
        random_id = random.randint(100000, 999999)
        
        if not tasks.find_one({"task_id": random_id}):
            tasks.insert_one(
                {
                    "ticket_id": random_id,
                    "name": name,
                    "description": "tbd",
                    "link": "tbd", 
                    "status": "opened"
                }
            )
            return random_id

#set link
def set_link(link: str, ticket_id: int):
    tasks.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "link": link,
                "description": f"Подписаться на - {link}",
            }
        }
    )


#get tasks
def get_tasks():
    return tasks.find()

#get task
def get_task(ticket_id: int) -> dict:
    return tasks.find_one({"ticket_id": ticket_id})

#insert completed task
def insert_completed(user_id: str, ticket_id: int):
    query = {"user_id": user_id}
    task = {
            'user_id': user_id,
            'ticket_id': ticket_id,
        }
    completed_tasks.insert_one(task)
    adref.update_one(query, {"$inc": {"completed_tasks": 1}})

#get completed task
def get_completed_tasks(user_id: str) -> dict:
    result = completed_tasks.find_one({"user_id": user_id})
    if result:
        return True
    else:
        False

#get individual task
def get_task_private(user_id: str, ticket_id: int) -> bool:
    content = completed_tasks.find_one({"user_id": user_id})
    if content:
        full_id = content.get("ticket_id")
        chunk_size = 6
        split_list = [str(full_id)[i:i+chunk_size] for i in range(0, len(str(full_id)), chunk_size)]
        target = ticket_id
        if target in split_list:
            return True
        else:
            return False

#update completed task
def update_completed(user_id: str, ticket_id: int):
    document = completed_tasks.find_one({"user_id": user_id})
    query = {"user_id": user_id}
    field_name = "ticket_id"
    new_value = ticket_id
    if document and field_name in document:
        current_value = str(document[field_name])
        updated_value = int(current_value + str(new_value))

        completed_tasks.update_one(query, {"$set": {field_name: updated_value}})
        print(user_id)
        print(type(user_id))
        adref.update_one(query, {"$inc": {"completed_tasks": 1}})

#delete task
def delete_task(ticket_id: str, user_id: str):
    tasks.delete_one({"ticket_id": ticket_id})
    filter = {"user_id": user_id}
    task_to_remove = ticket_id

    user_document = completed_tasks.find_one(filter)

    if user_document:
        task_ids = user_document.get("ticket_id", "")
        
        if task_to_remove in task_ids:
            updated_task_ids = task_ids.replace(task_to_remove, "")
            
            completed_tasks.update_one(filter, {"$set": {"ticket_id": updated_task_ids}})
            print("Идентификатор задания удалён.")
        else:
            print(f"Идентификатор {task_to_remove} не найден.")
    else:
        print("Пользователь не найден.")

#add referral
def add_referral(referrer_id: str):
    try:

        referrer = adref.find_one({"user_id": referrer_id})
        
        if referrer:

            invited_referrals = referrer.get("invited_referrals", 0) + 1

            new_balance = referrer.get("balance", 0) + 150

            result = adref.update_one(
                {"user_id": referrer_id},
                {
                    "$set": {"invited_referals": invited_referrals, "balance": new_balance}
                }
            )

            if result.modified_count > 0:
                print(f"User {referrer_id} updated successfully.")
            else:
                print(f"No update needed for user {referrer_id}.")
        else:
            print(f"Referrer with user_id {referrer_id} not found.")

    except Exception as e:
        print(f"Error updating referral data: {e}")