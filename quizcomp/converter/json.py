import os
import typing

import quizcomp.constants
import quizcomp.converter.converter
import quizcomp.converter.template
import quizcomp.question.base
import quizcomp.variant

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-json')

class JSONTemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to JSON using templates.
    """

    def __init__(self,
            format: str = quizcomp.constants.FORMAT_JSON,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(format, template_dir, **kwargs)

    # Simplify parts of the question context (specifically the answers) for testing.
    def modify_question_context(self,
            context: typing.Dict[str, typing.Any],
            question: quizcomp.question.base.Question,
            variant: quizcomp.variant.Variant) -> typing.Dict[str, typing.Any]:
        question_context = context['question']
        answers = question_context['answers']
        question_type = question_context['question_type']

        question_context['answers'] = self._clean_answers(answers, question_type)

        return context

    def _clean_answers(self,
            answers: typing.Union[None, typing.List[typing.Any], typing.Dict[str, typing.Any]],
            question_type: str,
            ) -> typing.Union[None, typing.List[typing.Any], typing.Dict[str, typing.Any]]:
        """ Clean a questions answers before output. """

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

    def _clean_answers_list(self,
            answers: typing.List[typing.Any],
            question_type: typing.Union[str, None],
            ) -> typing.List[typing.Any]:
        """ Clean a questions answers that are in a list format. """

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

    def _clean_answers_matching(self,
            answers: typing.Dict[str, typing.Any]
            ) -> typing.Dict[str, typing.Any]:
        """ Clean answers for a matching question. """

        return {
            'lefts': [self._clean_matching_item(item) for item in answers['lefts']],
            'rights': [self._clean_matching_item(item) for item in answers['rights']],
            'distractors': [item['raw_text'] for item in answers.get('distractors', [])],
        }

    def _clean_matching_item(self, item: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """ Clean a single matching item (answer component). """

        result = {
            'text': item['raw_text'],
            'id': item['id'],
        }

        if ('solution_id' in item):
            result['solution_id'] = item['solution_id']

        return result

class JSONConverter(quizcomp.converter.converter.Converter):
    """
    A converter to convert a quiz to JSON.
    The produced JSON will be more raw (less polished) than JSONTemplateConverter.
    """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def convert_variant(self, variant: quizcomp.variant.Variant, **kwargs: typing.Any) -> str:
        return variant.to_json()
