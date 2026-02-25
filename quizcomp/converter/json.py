"""
Convert a quiz to JSON.
"""

import os

import quizcomp.constants
import quizcomp.converter.converter
import quizcomp.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-json')

class JSONTemplateConverter(quizcomp.converter.template.TemplateConverter):
    def __init__(self,
            format = quizcomp.constants.FORMAT_JSON, template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(format, template_dir, **kwargs)

    # Simplify parts of the question context (specifically the answers) for testing.
    def modify_question_context(self, context, question, variant):
        question = context['question']
        answers = question['answers']
        question_type = question['question_type']

        question['answers'] = self._clean_answers(answers, question_type)

        return context

    def _clean_answers(self, answers, question_type):
        if (answers is None):
            # Seen in text only questions.
            return None

        if (isinstance(answers, list)):
            return self._clean_answers_list(answers, question_type)

        if (question_type == quizcomp.constants.QUESTION_TYPE_MATCHING):
            return self._clean_answers_matching(answers)

        if (question_type == quizcomp.constants.QUESTION_TYPE_NUMERICAL):
            return [raw_answer.to_pod() for raw_answer in answers['raw_answers']]

        if (question_type == quizcomp.constants.QUESTION_TYPE_FIMB):
            result = []
            for answer in answers.values():
                result.append({
                    'label': answer['raw_label'],
                    'solutions': [value['raw_text'] for value in answer['solutions']],
                })

            return result


        raise ValueError(f"Unknown answers type: '{type(answers)}'.")

    def _clean_answers_list(self, answers, question_type):
        for i in range(len(answers)):
            old_answer = answers[i]

            if (not isinstance(old_answer, dict)):
                old_answer = old_answer.to_pod()

            new_answer = {}

            if (question_type == quizcomp.constants.QUESTION_TYPE_MDD):
                new_answer['label'] = old_answer['raw_label']
                new_answer['choices'] = self._clean_answers_list(old_answer['choices'], None)
            else:
                text_keys = ['raw_text', 'text']
                for key in text_keys:
                    if (key in old_answer):
                        new_answer['text'] = old_answer[key]
                        break

                if ('correct' in old_answer):
                    new_answer['correct'] = old_answer['correct']

            answers[i] = new_answer

        return answers

    def _clean_answers_matching(self, answers):
        return {
            'lefts': [self._clean_matching_item(item) for item in answers['lefts']],
            'rights': [self._clean_matching_item(item) for item in answers['rights']],
            'distractors': [item['raw_text'] for item in answers.get('distractors', [])],
        }

    def _clean_matching_item(self, item):
        result = {
            'text': item['raw_text'],
            'id': item['id'],
        }

        if ('solution_id' in item):
            result['solution_id'] = item['solution_id']

        return result

class JSONConverter(quizcomp.converter.converter.Converter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def convert_variant(self, variant, **kwargs):
        return variant.to_json()
