# @file parse_descs.py
# @brief Parses course information from course descriptions pages on
#        http://coursecatalog.web.cmu.edu/ into an object.
# @author Justin Gallagher (jrgallag@andrew.cmu.edu)
# @since 2014-12-13


import sys
import urllib.request
import re
import bs4


# @function extract_num_name
# @brief Extracts the course number and name from a dt element from a
#        course description webpage.
# @param dtelement: <dt> element from a course description webpage.
# @return (num (string), name (string)): The course number and name.
def extract_num_name(dtelement):
    elements = dtelement.get_text().split(' ', 1)
    return (elements[0], elements[1])


# @function extract_units_semester_info
# @brief Extracts the number of units and semesters offered from a text
#        line.
# @param line (string): A text line containing one or both of the units
#        awarded or semesters offered by a course, in the form
#        '[semesters]:[units]' or '[semesters]' or '[units]'. The
#        'units' component must contain a number.
# @return (units (float), semester ([string])): The number of units that
#        the course awards, and a list of the semesters that it is
#        offered, where 'F' is fall, 'S' is spring, and 'U' is summer.
def extract_units_semester_info(line):
    parts = line.split(':')

    # Extract relevant parts
    if len(parts) == 2:
        semester_text = parts[0]
        units = float(re.sub('[^0-9.]', '', parts[1]))
    elif 'unit' in parts[0]:
        semester_text = 'All Semesters'
        units = float(re.sub('[^0-9.]', '', parts[0]))
    else:
        semester_text = parts[0]
        units = 0.0

    # Parse semesters
    semester = []
    if 'Fall' in semester_text:
        semester.append('F')
    if 'Spring' in semester_text:
        semester.append('S')
    if 'Summer' in semester_text:
        semester.append('M')
    if 'All' in semester_text:
        semester = ['F', 'S', 'M']

    return (units, semester)


# @function: split_course_list
# @brief: Creates a list from a string by splitting it at the given conjunction
#        and then formats the list by removing whitespace and parentheses
#        around each list element.
# @param reqs: A string of required prerequisites/corequisites.
# @param conj: A string of a conjunction word {'and', 'or'} to be used as the
#        argument for the split() function.
# @return: The formatted list generated by the split() function.
def split_course_list(reqs, conj):
    split_list = reqs.split(conj)
    formatted_list = []
    for item in split_list:
        formatted_item = item.strip().strip('()')
        formatted_list.append(formatted_item)
    return formatted_list


# @function: is_inverted
# @brief: Determines whether the data structure should be inverted
#         by using regex to determine whether the expression
#         "(xx-xxx and xx-xxx"  is present; the x's represent any digit 0-9.
# @param reqs: A string of required Prerequisites/Corequisites.
# @return: Boolean.
def is_inverted(reqs):
    and_groups = re.findall(r'\((\d{2})(-)(\d{3}) and (\d{2})(-)(\d{3})', reqs)
    return len(and_groups) > 0


# @function: create_reqs_list
# @brief: Creates a 2-dimensional list given the reqs string and the
#         principal conjunction.
# @param reqs: A string of required prerequisites/corequisites.
# @param conj: A string of a conjunction word {'and', 'or'}.
# @return: 2-dimensional list representation of the prerequisites/corequisites.
def create_reqs_list(reqs, conj):

    # Separates the requisites into course groups by the given conjunction
    course_groups = split_course_list(reqs, conj)
    anti_conj = 'or' if conj == 'and' else 'and'
    reqs_list = []

    for course_group in course_groups:
        inner_list = []
        courses = split_course_list(course_group, anti_conj)

        for course in courses:
            formatted_str = course.strip()
            inner_list.append(formatted_str)

        reqs_list.append(inner_list)

    return reqs_list


# @function: create_reqs_obj
# @brief: Creates an object representation of the given prerequisites/
#         corequisites.
# @param reqs: A string of required prerequisites/corequisites.
# @return: {'invert': Boolean indicating whether the representation is inverted,
#           'reqs_list': List representation of the prerequisites/corequisites}.
def create_reqs_obj(reqs):
    if reqs == '':
        invert = None
        reqs_list = None
    elif is_inverted(reqs):
        invert = True
        reqs_list = create_reqs_list(reqs, 'or')
    else:
        invert = False
        reqs_list = create_reqs_list(reqs, 'and')
    return {'invert': invert, 'reqs_list': reqs_list}


# @function extract_desc_prereqs_coreqs
# @brief Extracts the course description, prerequisites and
#        corequisites from an array of strings.
# @param blocks ([string]): An array of strings containing parts of the
#        course description and the course prerequisites (starting with
#        'Prerequisite: ' or 'Prerequisites: ' and corequisites
#        (starting with 'Corequisite: ' or 'Corequisites: '.
# @return (desc(string), prereqs(string), coreqs(string)): Course
#        description, course prerequisites, and course corequisites
#        respectively.
def extract_desc_prereqs_coreqs(blocks):
    prereqs = ''
    coreqs = ''
    desc = ''
    for item in blocks:
        item = item.strip()
        if item.startswith('Prerequisite: '):
            prereqs = item.strip('Prerequisite: ')
        elif item.startswith('Prerequisites: '):
            prereqs = item.strip('Prerequisites: ')
        elif item.startswith('Corequisite: '):
            coreqs = item.strip('Corequisite: ')
        elif item.startswith('Corequisites: '):
            coreqs = item.strip('Corequisite: ')
        else:
            if (desc != ''):
                desc += ' '
            desc += item

    # Fix odd spacing
    desc = ' '.join(desc.split())

    return (desc, prereqs, coreqs)


# @function extract_course_info
# @brief Extracts course information from a <dt> html element.
# @param dlelement: <dt> element from a course description web page.
# @return {'num': Course number
#          'name': Course name
#          'units': Units awarded
#          'semester': Semesters offered
#          'desc': Course description
#          'prereqs': Course prerequisites
#          'coreqs': Course corequisites }
def extract_course_info(dlelement):
    # Get course number and title
    (num, name) = extract_num_name(dlelement.find('dt', class_='keepwithnext'))

    desc_block = dlelement.find('dd')

    # Remove html elements
    for item in desc_block.find_all(re.compile('^(?!br).*$')):
        item.replace_with(item.get_text())
    block_raw = desc_block.decode(formatter=None)
    block_raw = block_raw.replace('<dd>', '').replace('</dd>', '')
    blocks = re.split('<br>|<br/>', block_raw)

    # Get units and semester info
    if len(blocks[0]) < 100:
        (units, semester) = extract_units_semester_info(blocks.pop(0))
    else:
        (units, semester) = (0.0, ['F', 'S', 'U'])

    # Get description
    (desc, prereqs, coreqs) = extract_desc_prereqs_coreqs(blocks)
    prereqs_obj = create_reqs_obj(prereqs)
    coreqs_obj  = create_reqs_obj(coreqs)
    return {'num': num, 'name': name, 'units': units, 'semester': semester,
            'desc': desc, 'prereqs': prereqs, 'prereqs_obj': prereqs_obj,
            'coreqs': coreqs, 'coreqs_obj': coreqs_obj}


# @function extract_courses
# @brief Extracts course blocks from a page object.
# @param page: Page object to get blocks from.
# @return: Array of course objects found on page.
def extract_courses(page):
    return page('dl', class_='courseblock')


# @function get_page
# @brief Gets a webpage as an object
# @param url: URL of the page to get.
# @return: The page as a BeautifulSoup html object, or None if an error
#        occurred.
def get_page(url):
    try:
        response = urllib.request.urlopen(url)
    except (urllib.request.URLError, ValueError):
        return None

    return bs4.BeautifulSoup(response.read(), 'html.parser')


# @function parse_descs
# @brief Parses course descriptions from links in a file, and writes
#        them as JSON to the output file.
# @param inpath: File path for a text file containing fully qualified
#        URLS for course description pages, separated by newlines.
# @return: Course desciption data as a list.
def parse_descs(inpath):
    # Array of result course information
    results = []

    # Get information
    with open(inpath, 'r') as infile:
        print('Getting data from:')

        # Read links from file
        for line in infile:
            print('    ' + line.strip() + ': ', end='', flush=True)

            # Get data
            page = get_page(line.strip())
            if not page:
                print('Failed!')
                continue

            # Separate out course elements
            courses = extract_courses(page)

            # Get info for each course and add to list
            for course in courses:
                results.append(extract_course_info(course))

            print('Success!')

    return results
