$(function() {

    $.getJSON( "http://dash_api.shawk.in/graph_data/market/days=1/", function( data ) {
        console.log(data.last);

        $.each(data.types, function(idx, obj){
            setTimeout(function(){

                var chart = Morris.Line({
                    element: 'morris-' + obj,
                    data: data.long_term_averages,
                    xkey: 'morris_date',
                    ykeys: [obj+'avg_sell', obj+'sell'],
                    labels: ['Average', 'Current'],
                    pointSize:0,
                    hideHover: 'auto',
                    resize: true,
                    ymin: 'auto',
                    lineColors: ['#1f77b4', '#ff7f0e']
                });

                if (0 == idx) {
                    chart.options.labels.forEach(function(label, i) {
                        var legendItem = $('<span></span>').text(label).css('color', chart.options.lineColors[i]);
                        $('.legend').append(legendItem);
                    });
                }

                var diff = 100 * ((data.last[obj+"sell"] - data.last[obj+"avg_sell"]) / (0.5 * (data.last[obj+"avg_sell"] + data.last[obj+"sell"])));
                var diff_text;
                var color;
                if(diff > 0) {
                    color = "green";
                    diff_text = "+" + diff.toFixed(2) + "%";
                } else {
                    color = "red";
                    diff_text = diff.toFixed(2) + "%";
                }
                console.log(obj + ": " + data.last[obj+"avg_sell"] + " -- " + data.last[obj+"sell"] +" = "+ diff);
                var cost_elem = $("#"+obj+"-cost");
                var percent_elem = $("#"+obj+"-percent");
                var loading_elem = $("#"+obj+"-loading");
                cost_elem.html("<span style='color: "+color+"'>$"+data.last[obj+"sell"] + "</span>");
                cost_elem.hide().show(0);
                percent_elem.html("<span style='color: "+color+"'>"+diff_text+"</span>");
                percent_elem.hide().show(0);
                loading_elem.hide();
            }, idx*500);
        });
});

    //Morris.Area({
    //    element: 'morris-area-chart',
    //    data: [{
    //        period: '2010 Q1',
    //        iphone: 2666,
    //        ipad: null,
    //        itouch: 2647
    //    }, {
    //        period: '2010 Q2',
    //        iphone: 2778,
    //        ipad: 2294,
    //        itouch: 2441
    //    }, {
    //        period: '2010 Q3',
    //        iphone: 4912,
    //        ipad: 1969,
    //        itouch: 2501
    //    }, {
    //        period: '2010 Q4',
    //        iphone: 3767,
    //        ipad: 3597,
    //        itouch: 5689
    //    }, {
    //        period: '2011 Q1',
    //        iphone: 6810,
    //        ipad: 1914,
    //        itouch: 2293
    //    }, {
    //        period: '2011 Q2',
    //        iphone: 5670,
    //        ipad: 4293,
    //        itouch: 1881
    //    }, {
    //        period: '2011 Q3',
    //        iphone: 4820,
    //        ipad: 3795,
    //        itouch: 1588
    //    }, {
    //        period: '2011 Q4',
    //        iphone: 15073,
    //        ipad: 5967,
    //        itouch: 5175
    //    }, {
    //        period: '2012 Q1',
    //        iphone: 10687,
    //        ipad: 4460,
    //        itouch: 2028
    //    }, {
    //        period: '2012 Q2',
    //        iphone: 8432,
    //        ipad: 5713,
    //        itouch: 1791
    //    }],
    //    xkey: 'period',
    //    ykeys: ['iphone', 'ipad', 'itouch'],
    //    labels: ['iPhone', 'iPad', 'iPod Touch'],
    //    pointSize: 2,
    //    hideHover: 'auto',
    //    resize: true
    //});

    Morris.Donut({
        element: 'morris-donut-chart',
        data: [{
            label: "Download Sales",
            value: 12
        }, {
            label: "In-Store Sales",
            value: 30
        }, {
            label: "Mail-Order Sales",
            value: 20
        }],
        resize: true
    });

    Morris.Bar({
        element: 'morris-bar-chart',
        data: [{
            y: '2006',
            a: 100,
            b: 90
        }, {
            y: '2007',
            a: 75,
            b: 65
        }, {
            y: '2008',
            a: 50,
            b: 40
        }, {
            y: '2009',
            a: 75,
            b: 65
        }, {
            y: '2010',
            a: 50,
            b: 40
        }, {
            y: '2011',
            a: 75,
            b: 65
        }, {
            y: '2012',
            a: 100,
            b: 90
        }],
        xkey: 'y',
        ykeys: ['a', 'b'],
        labels: ['Series A', 'Series B'],
        hideHover: 'auto',
        resize: true
    });

});
