/**
 * Find a JSONEditor instance from it's container element or id
 * @param {string | Element} selector  A query selector id like '#myEditor'
 *                                     or a DOM element
 * @return {JSONEditor | null} Returns the created JSONEditor, or null otherwise.
 */
function findJSONEditor (selector) {
    var container = (typeof selector === 'string')
        ? document.querySelector(selector)
        : selector;

    return container && container.jsoneditor || null;
}

/**
 * Overwrites obj1's values with obj2's and adds obj2's if non existent in obj1
 * @param obj1
 * @param obj2
 * @returns obj3 a new object based on obj1 and obj2
 */
function merge_options(obj1,obj2){
    var obj3 = {};
    for (var attrname in obj1) { obj3[attrname] = obj1[attrname]; }
    for (var attrname in obj2) { obj3[attrname] = obj2[attrname]; }
    return obj3;
}

/**
 * Generates all cases of elements using the first element in the fieldnames as object-key
 * @param elements: array of array objects
 * @param fieldnames: array of string with fields (elements.length == fieldnames.length)
 * @returns {*}
 */
function allCases(elements, fieldnames) {
    var results = [];
    if (elements.length === 0) {
        return {};
    } else if (elements.length === 1) {
        var fieldname = fieldnames[0];
        var element = elements[0];

        var results = [];
        $.each(element, function(i, item) {
            var obj = {};
            obj[fieldname] = item;
            results.push(obj)
        });
        return results;
    }
    $.each(elements[0], function(i, item) {
        var current_label = fieldnames[0];
        var obj = {};
        obj[current_label] = item;

        var rest_cases = allCases(elements.slice(1), fieldnames.slice(1));
        if (Array.isArray(rest_cases)) {
            $.each(rest_cases, function(new_element_id, new_element) {
                new_obj = merge_options(obj, new_element);
                results.push(new_obj);
            });
        } else {
            new_obj = merge_options(obj, rest_cases);
            results.push(new_obj);
        }
    });
    return results;
}

$(document).ready(function() {
    $('.row .newelement_typeselection a').on('click', function () {
        event.preventDefault();
        var targetname = $(this).attr('name');
        $(this).closest('ul').find('li.active').removeClass('active');
        $(this).closest('li').addClass('active');
        $('div.selectiontype').removeClass('active');
        $('#' + targetname).addClass('active');
    });
});

