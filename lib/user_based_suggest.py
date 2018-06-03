from . import utils

import numpy

from multiprocessing.pool import ThreadPool


def get_resource_set(solved_matrix,
                     base_resource_index
                    ):
    resource_set = set()
    for index, score in enumerate(solved_matrix[:, base_resource_index]):
        if score == 1:
            resource_set.add(index)
    return resource_set


def get_user_set(solved_matrix,
                 base_user_index,
                 are_similar_users
                ):
    user_set = set()
    for index, score in enumerate(solved_matrix):
        if index == base_user_index:
            continue
        if are_similar_users(solved_matrix[base_user_index], solved_matrix[index]):
            user_set.add(index)
    return user_set


def are_similar_by_corrcoef(first_row,
                            second_row,
                            alpha=0.4
                           ):
    return numpy.corrcoef(first_row, second_row)[0][1] > alpha


def get_dist_between_sets(first_set,
                          second_set
                         ):
    return len(first_set & second_set) / len(first_set | second_set)


def user_based_suggest(solved_matrix,
                       base_user_index,
                       are_similar_users
                      ):
    base_user_set = get_user_set(
        solved_matrix=solved_matrix,
        base_user_index=base_user_index,
        are_similar_users=are_similar_users
    )
    
    suggestions = []
    for suggest_index in range(solved_matrix.shape[1]):
        if solved_matrix[base_user_index][suggest_index] != 0:
            continue
        resource_set = get_resource_set(
            solved_matrix=solved_matrix,
            base_resource_index=suggest_index
        )
        score = get_dist_between_sets(
            first_set=base_user_set,
            second_set=resource_set
        )
        suggestions.append(
            utils.SingleSuggest(
                problem_index=suggest_index,
                score=score
            )
        )
    return sorted(suggestions, key=lambda s: s.score, reverse=True)


def suggest(timus,
            top_size
           ):
    solved_matrix, authors_encoder, problems_encoder = utils.build_solved_matrix(timus)
    
    def process(user_index):
        return user_based_suggest(
            solved_matrix=solved_matrix,
            base_user_index=user_index,
            are_similar_users=are_similar_by_corrcoef
        )
    
    with ThreadPool() as pool:
        all_suggestions = [
            suggest[:top_size]
            for suggest in pool.map(process, range(solved_matrix.shape[0]))
        ]
    suggestions = dict()
    for user_index, suggest in enumerate(all_suggestions):
        suggestions[authors_encoder.decode(user_index)] = [
            utils.SingleSuggest(
                problem_index=problems_encoder.decode(suggestion.problem_index),
                score=suggestion.score
            )
            for suggestion in all_suggestions[user_index]
        ]
    return suggestions
