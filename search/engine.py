from taggit.models import Tag

from search.models import Gif, TagInstance


common_words = ('the', 'and', 'a', 'that', 'i', 'it',
    'not', 'he', 'as', 'you', 'this', 'but', 'his', 'they',
    'her', 'she', 'or', 'an', 'to', 'of', 'in', 'for', 'on',
    'with', 'at', 'by', 'from')

synonyms = (['anger', 'angry', 'mad', 'upset', 'unhappy'],
    ['happy', 'happiness'],
    ['fear', 'afraid', 'scared', 'worried'],
    ['clap', 'clapping', 'applause'], ['dance', 'dancing'],
    ['agreement', 'approval'],
    ['disagreement', 'disapproval'],
    ['boobs', 'breasts', 'tits'])

class Result(object):
    def __init__(self, gif, rank):
        self.gif = gif
        self.rank = rank

def query(query_string):
    # create an empty match list
    match_list = []
    query_string = query_string.lower()
    # split the query into a list of individual words
    query_words = query_string.split(' ')[:10] # limit the query to 10 words
    query_words = removeSynonyms(query_words)
    for word in query_words:
        if commonWord(word):
            continue # skip if common word
        else:
            synonyms = synonym(word)
            if not synonyms:
                check(word, match_list)
            else:
                for word in synonyms:
                    check(word, match_list)
    match_list.sort(key=lambda x: x.rank, reverse=True)
    return match_list

def commonWord(word):
    '''checks if word passed is common or not'''
    return word in common_words

def synonym(word):
    '''checks if word is a synonym. returns a list or a boolean'''
    for word_group in synonyms:
        if word in word_group:
            return word_group
    return None

def removeSynonyms(_list):
    '''removes synonyms from the query'''
    for synonym_entry in synonyms:
        already_matched = False
        # traverse the list backwards to prevent .index() problems
        # remove all common synonyms except the last one
        for word in reversed(_list):
            if already_matched and word in synonym_entry:
                _list.pop(_list.index(word))
            elif word in synonym_entry:
                already_matched = True
    return _list

def check(word, match_list):
    '''checks for a match'''
    matching_tags = Tag.objects.filter(name__contains=word)
    for tag in matching_tags:
        instances = TagInstance.objects.filter(tag=tag)\
                                       .select_related('content_object')
        for instance in instances:
            gif = instance.content_object
            match(gif, word, match_list)

def match(gif, word, match_list):
    '''adds a match'''
    # check to see if a match has already been found on this image
    for entry in match_list:
        if entry.gif == gif:
            entry.rank += 1
            return match_list
    # if the match is not already in the list, append it with the match counter set at 1
    match_list.append(Result(gif, 1))
    return match_list
