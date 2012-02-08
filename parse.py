#!/usr/bin/python
import re, os, sys, random
from subprocess import call
print "starting"
def split_on(xs, pred):
    """Split xs into a list of lists each beginning with the next x
    satisfying pred, except possibly the first"""
    indices = [i for (i,v) in enumerate(xs) if pred(v)]
    return [xs[i:j] for (i,j) in zip([0]+indices,indices+[len(xs)]) if i != j]

def extract_on_context(xs, pred):
    """extract from xs  a list of lists, each beginning and ending with
    an element satisfying pred"""
    indices = [i for (i,v) in enumerate(xs) if pred(v)]
    index_sets = [(indices[i],indices[i+1]) for i in range(len(indices)) if i % 2 == 0]
    return [xs[i:j+1] for (i,j) in index_sets]

def extract_questions(xs):
    marks_a_question = lambda(line):re.search(r"{question}", line)
    return extract_on_context(xs,marks_a_question)

def split_into_blocks(lines):
    """Return list of list of lines, each list representing a block
    from which one question is to be chosen"""
    starts_a_block = lambda(line):re.search(r"begin{block}", line)
    return [block for block in split_on(lines,starts_a_block) if len(block) > 1]

def screen_blocks(lines):
    marks_a_block = lambda(line):re.search(r"{block}", line)
    return [line for line in lines if not marks_a_block(line)]
    
def remove_sublist(xs,ys):
    """Return list xs minus sublist ys"""
    if not xs:
        return xs
    elif startswith(xs,ys):
        return xs[len(ys):]
    else:
        return [xs[0]] + remove_sublist(xs[1:],ys)
    
def startswith(xs,ys):
    return ys == xs[:len(ys)]
    
def select_question_from_block(block):
    """Accept a block, return a block with at most a single question"""
    starts_a_question = lambda(line):re.search(r"begin{question}", line)
    if(any(map(starts_a_question,block))):
        questions = extract_questions(block)
        print("block contains %s questions:" % len(questions))
        for q in questions:
            print q
        print("I choose question:")
        question = random.choice(questions)
        print question
        print
        bad_questions = [q for q in questions if q != question]
        result_block = reduce(lambda b,bq:remove_sublist(b,bq),bad_questions, block)
        return scramble_choices(screen_empty_environments(screen_blocks(result_block)))
    else:
        return block[1:]

def interleave(xs,ys):
    """Pair adjacent indices"""
    return [(x,y) for x in xs for y in ys if x + 1 == y]

def screen_empty_environments(lines):
    begins = lambda(line):re.search("begin{",line)
    ends = lambda(line):re.search("end{",line)
    begin_indices = [i for i,line in enumerate(lines) if begins(line)]
    end_indices = [i for i,line in enumerate(lines) if ends(line)]
    empty_environment_indices = sum(interleave(begin_indices,end_indices),())
    return [line for i,line in enumerate(lines) if not i in empty_environment_indices]

def scramble_choices(lines):
    """Scramble adjacent multiple choice sublists"""
    marks_a_choice = lambda(line):re.search(r"\\choice", line)
    outlines = []
    current_group = []
    for line in lines:
        if marks_a_choice(line):
            current_group.append(line)
        else:
            if current_group:
                random.shuffle(current_group)
                outlines += current_group
                current_group = []
                outlines.append(line)
            else:
                outlines.append(line)
    return outlines

def adjacents(xs):
    return zip([None]+xs,xs)[1:]

def make_question_versioner(question_bank):
    question_versions = []
    ranges = map(len, question_bank)
    def question_versioner():
        version = map(random.randrange,ranges)
        if not version in question_versions:
            question_versions.append(version)
            return version
        else:
            return question_versioner()
    return question_versioner

def get_questions_from_version(question_bank, version):
    return sum(map(lambda(q,v): q[v],zip(question_bank,version)),[])
    
def make_version(version_number,versioner):
    date_string = {
                   0:"Tuesday 4pm",
                   1:"Tuesday 5pm",
                   2:"Wednesday 5pm",
                   3:"Thursday 3pm",
                   4:"Monday 5pm",
                   5:"Tuesday 3pm",
                   6:"Thursday 4pm",
                   7:"Thursday 5pm"
                   }
    
    version_selections = versioner()
    print("starting on %s" % version_number)
    #questions = get_questions_from_version(question_bank, version_selections)
    questions = sum(map(select_question_from_block,blocks),[])
    final_preamble = "".join(versioned_preamble) % date_string[version_number]
    
    text = final_preamble + "".join(questions)
    return text

def unique(xs):
    if not xs:
        return True
    else:
        x = xs[0]
        rest = xs[1:]
        return (not x in rest) and unique(rest)

def make_unique_versions(num_versions,versioner):
    versions = []
    while len(versions) < num_versions:
        version = make_version(len(versions),versioner)
        if not version in versions:
            versions.append(version)
    return versions

def generate_quiz(quiz_text,version_num):
    name, ext = os.path.splitext(filename)
    outfile = name + chr(version_num + 97)+ext
    print("now working: ", outfile)
    print(quiz_text)
    with open(outfile,'w') as g:
        g.write(quiz_text)
    command = "pdflatex -quiet " + outfile
    print(command)
    call("pdflatex " + outfile,shell=True)

    
if __name__ == "__main__":
    print "in the main"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "quiz1.tex"
        
    with open(filename) as f:
        lines = f.readlines()

    num_versions = int(re.search("NumberOfVersions{(\d)}","".join(lines)).group(1))
    chunks = split_into_blocks(lines)
    preamble, blocks = chunks[0],chunks[1:]
    sectioned_preamble = map(lambda(line):re.sub("Week","%s Week",line),preamble)
    versioned_preamble = map(lambda(line):re.sub("NumberOfVersions{(\d)}",
                                                 "NumberOfVersions{1}",line),
                             sectioned_preamble)
    question_bank = map(extract_questions,blocks)
    versioner = make_question_versioner(question_bank)
    quiz_texts = make_unique_versions(num_versions,versioner)

    for version_num, quiz_text in enumerate(quiz_texts):
        generate_quiz(quiz_text,version_num)
