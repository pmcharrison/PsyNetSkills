class VariableHandler:
    @staticmethod
    def get_value(participant, variable):
        return getattr(participant.var, variable) if participant.var.has(variable) else None

    @staticmethod
    def set_value(participant, variable, value):
        setattr(participant.var, variable, value)

    @staticmethod
    def get_from_answer(answer, variable):
        if not answer:
            return None
        values = [
            value for key, value in answer.items()
            if key.startswith(variable) and value not in (None, 'null', 'INVALID_RESPONSE')
        ]
        return values[0] if len(values) == 1 else None

    @staticmethod
    def get_value_from_last_answer(participant, page_label):
        if not participant.answer_accumulators:
            return None
        return VariableHandler.get_from_answer(participant.answer_accumulators[-1], page_label)
