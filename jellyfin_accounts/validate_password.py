specials = ['[', '@', '_', '!', '#', '$', '%', '^', '&', '*', '(', ')',
            '<', '>', '?', '/', '\\', '|', '}', '{', '~', ':', ']']


class PasswordValidator:
    def __init__(self, min_length, upper, lower, number, special):
        self.criteria = {
            "characters": int(min_length),
            "uppercase characters": int(upper),
            "lowercase characters": int(lower),
            "numbers": int(number),
            "special characters": int(special),
        }

    def validate(self, password):
        count = {
            "characters": 0,
            "uppercase characters": 0,
            "lowercase characters": 0,
            "numbers": 0,
            "special characters": 0,
        }
        for c in password:
            count["characters"] += 1
            if c.isupper():
                count["uppercase characters"] += 1
            elif c.islower():
                count["lowercase characters"] += 1
            elif c.isnumeric():
                count["numbers"] += 1
            elif c in specials:
                count["special characters"] += 1
        for criterion in count:
            if count[criterion] < self.criteria[criterion]:
                count[criterion] = False
            else:
                count[criterion] = True
        return count

    def getCriteria(self):
        lines = {}
        for criterion in self.criteria:
            min = self.criteria[criterion]
            if min > 0:
                text = f"Must have at least {min} "
                if min == 1:
                    text += criterion[:-1]
                else:
                    text += criterion
                lines[criterion] = text
        return lines
