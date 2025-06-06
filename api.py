from enum import Enum
import json
from random import choice

from fastapi import FastAPI, Query
from pydantic import BaseModel


app = FastAPI(description="An API to find clues for crossword answers.")


class DistanceMode(str, Enum):
    same = "same"
    longer = "longer"
    shorter = "shorter"
    any = "any"


class RandomResponse(BaseModel):
    answer: str | None = None
    clue: str | None = None
    msg: str = "Success"


class CluesResponse(BaseModel):
    answer: str
    clues: list[str]


def load_data():
    with open("clues.json", "r") as data_file:
        tmp = json.load(data_file)
    out = {}
    for x in tmp:
        out[int(x)] = tmp[x]
    return out


def edit_distance(x, y):
    distance = 0
    for a, b in zip(x, y):
        if a != b:
            distance += 1
    return distance


def levenshtein_distance(s1, s2):
    # https://stackoverflow.com/questions/2460177/edit-distance-in-python
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


def collect_answers_mode_any(previous, length, distance, data):
    out = []
    for l in range(length-distance, length+distance+1):
        try:
            out.extend([x for x in data[l].keys() if levenshtein_distance(x, previous) == distance])
        except KeyError:
            pass
    return out


@app.get("/random", response_model=RandomResponse, description="Return a radom answer-clue combination.")
def random_answer(length: int | None = Query(None, description="The length of the answer to be returned. Ignored if `previous` is provided."), 
                  previous: str | None = Query(None, description="The returned answer will be `distance` characters different from this \"previous\" answer."), 
                  distance: int = Query(1, description="Edit distance, relative to `previous`. Ignored if `previous` is not provided."),
                  distance_mode: DistanceMode = Query(DistanceMode.same, description="Whether the returned answer may be longer or shorter than the `previous` answer. Ignored if `previous` is not provided.")):
    data = load_data()
    
    if previous is not None:
        length = len(previous)
        previous = previous.upper()
    elif length is None:
        length = choice(list(data.keys()))

    if previous is not None:
        try:
            match distance_mode:
                case DistanceMode.same: possible_answers = [x for x in data[length].keys() if edit_distance(x, previous) == distance]
                case DistanceMode.longer: possible_answers = [x for x in data[length+distance].keys() if levenshtein_distance(x, previous) == distance]
                case DistanceMode.shorter: possible_answers = [x for x in data[length-distance].keys() if levenshtein_distance(x, previous) == distance]
                case DistanceMode.any: possible_answers = collect_answers_mode_any(previous, length, distance, data)
        except KeyError:
            return {"msg": f"No possible answers with the expected length."}
    else:
        try:
            possible_answers = list(x for x in data[length].keys())
        except KeyError:
            return {"msg": "No known answers for the given length."}

    try:
        answer = choice(possible_answers)
    except IndexError:
        return {"msg": "No possible answers with the expected distance."}

    clue = choice(list(data[len(answer)][answer]))
    return {"answer": answer, "clue": clue}


@app.get("/clues", response_model=CluesResponse, description="Return all known clues for the given `answer`.")
def all_clues(answer: str = Query(description="The answer to retrieve the clues for.")):
    answer = ''.join(list([x.upper() for x in answer if x.isalpha()]))
    length = len(answer)
    data = load_data()

    try:
        return {"answer": answer, "clues": data[length][answer]}
    except KeyError:
        return {"answer": answer, "clues": []}
