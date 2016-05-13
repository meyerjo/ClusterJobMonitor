

$(document).ready(function() {
    $('.morris_chartarea').each(function(i, obj) {
        $.ajax('/dashboard/' + $(obj).attr('id') + '/json').done(function(data) {
            console.log(data)
            if ('charttype' in data) {
                if (data['charttype'] == 'bar') {
                    data = data['data'];
                    Morris.Bar(data);
                }
                else if (data['charttype'] == 'line') {
                    data = data['data'];
                    Morris.Line(data);
                } else if (data['charttype'] == 'donut') {
                    data = data['data'];
                    Morris.Donut(data);
                }
                else
                {
                    console.log(data);
                }
            }
        });
    });
});