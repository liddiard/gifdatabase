from search.models import Gif

common_words = ('the', 'and', 'a', 'that', 'i', 'it',
    'not', 'he', 'as', 'you', 'this', 'but', 'his', 'they',
    'her', 'she', 'or', 'an', 'to', 'of', 'in', 'for', 'on',
    'with', 'at', 'by', 'from')

synonyms = (['anger', 'angry', 'mad', 'upset', 'unhappy'],
    ['happy', 'happiness'],
    ['fear', 'afraid', 'scared', 'worried'],
    ['clap', 'clapping', 'applause'], ['dance', 'dancing'],
    ['agreement', 'approval'],
    ['disagreement', 'disapproval'])

class Result(object):
    def __init__(self, gif, rank):
        self.gif = gif
        self.rank = rank

def query(query_string):
    # create an empty match list
    match_list = []
    # split the query into a list of individual words
    query_words = query_string.split(' ')
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
                    check(item, match_list)
    return match_list

def commonWord(word):
    '''checks if word passed is common or not'''
    if word in common_words:
        return True
    else:
        return False

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

def tagSEO(gif):
    '''returns a sanitized list of individual words from a gif's tags'''
    seo = []
    tags = gif.tags.names()
    for tag in tags:
        words = tag.split(' ')
        for word in words:
            if commonWord(word):
                continue # skip if common word
            else:
                seo.append(word)
    return removeSynonyms(seo)

def check(word, match_list):
    '''checks for a match'''
    for gif in Gif.objects.all():
        tags = tagSEO(gif)
        if word in tags:
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