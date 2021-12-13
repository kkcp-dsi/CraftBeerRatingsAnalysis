// This is what I need to compute kernel density estimation
    function kde(kernel, thresholds, data) {
      return thresholds.map(t => [t, d3.mean(data, d => kernel(t - d))]);
    }
    
    function epanechnikov(bandwidth) {
      return x => Math.abs(x /= bandwidth) <= 1 ? 0.75 * (1 - x * x) / bandwidth : 0;
    }
    
    function create_svg(d3_html_element, _margin, _height, _width, _xAxis, _yAxis, _xAxisName){
      // append the svg object to the body of the page
      var _svg = d3_html_element.append("svg")
        .attr("width", _width + _margin.left + _margin.right)
        .attr("height", _height + _margin.top + _margin.bottom)
      .append("g")
        .attr("transform", "translate(" + _margin.left + "," + _margin.top + ")");
        
      _svg.append("g")
      .attr("class", "density")
    
      _svg.append("g")
        .attr("class", "xAxis")
        .attr("transform", "translate(0," + _height + ")")
        .call(_xAxis);
                  
      _svg.append("g")
        .attr("class", "yAxis")
        .call(_yAxis);
        
      // Add X axis label:
      _svg.append("text")
          .attr("text-anchor", "end")
          .attr("x", _width)
          .attr("y", _height + 40)
          .text(_xAxisName);
      return _svg;
    }
    
    function compute_density(states, state_data, ticks)
    {
      var allDensity = [];
      for (i in states){
        var state = states[i]
        var density = kde(epanechnikov(0.3), ticks, state_data[state]);
        allDensity.push({
          key: state,
          median: d3.median(state_data[state]),
          density: density
        });
        
        allDensity = allDensity.sort(function(x, y){
           return d3.descending(x.median, y.median);
        });
      }
      return allDensity;
    }
    
    function update(_svg, allDensity, lineGenerator){
      // Add areas
      var all_density_curves = _svg.select(".density")
        .selectAll("path")
        .data(allDensity, d=>d.key);
      
      all_density_curves.join("path")
        .attr("transform", function(d){return("translate(0," + (yName(d.key) - height) +")")})
        .attr("fill", d=>myColor(d.key))
        .attr("data-id", d=>d.key)
        .datum(d=>d.density)
        .transition()
        .duration(500)
        .attr("opacity", 0.5)
        .attr("stroke", "#000")
        .attr("stroke-width", 0.1)
        .attr("d", lineGenerator);
      
      _svg.select('.yAxis').call(yAxis);
      
      _svg.selectAll('path').on("click", function (event){
        var density_key = event.target.getAttribute('data-id');
        console.log(density_key);
      });
    }
    
    function update_hist(_svg, _bins, _xScaleYear, _yScaleYear)
    {
      var all_recs = _svg.select(".density")
        .selectAll("rect")
        .data(_bins, d=>d.key);
      
      var yScaleYearDomainMax = _yScaleYear.domain()[1];
      _yScaleYear.domain([0, yScaleYearDomainMax + 150 * yName.domain().length]);
      
      all_recs.enter().append("rect")
        .attr("class", "bar")
        .merge(all_recs)
        .attr("transform", function(d){
          return("translate(" + _xScaleYear(d.x0) + "," + (yName(d.color) + _yScaleYear(d.length) - height) +")")
        })
        .attr("data-id", d=>d.color)
        .transition()
        .duration(500)
        .ease(d3.easeLinear)
        .attr("fill", d => myColor(d.color))
        .attr("width", d => _xScaleYear(d.x1) - _xScaleYear(d.x0))
        .attr("height", d => height - _yScaleYear(d.length));
      
      all_recs
          .exit()
          .transition()
          .duration(500)
          .ease(d3.easeLinear)
          .attr("height", 0)
          .remove();
      
      _svg.select('.yAxis').call(yAxis);
      
      _yScaleYear.domain([0, yScaleYearDomainMax]);
      
      _svg.selectAll('rect').on("click", function (event){
        var density_key = event.target.getAttribute('data-id');
        console.log(density_key);
      });
    }
    
    function update_state_hist(_bins, _svg, _xScaleState, _yScaleState, _xAxisState, _yAxis, _colorGenerator){
      
      var yScaleYearDomainMax = _yScaleState.domain()[1];
      _yScaleState.domain([0, yScaleYearDomainMax + 1500 * yName.domain().length]);
      
      var all_recs = _svg.select(".density")
        .selectAll("rect")
        .data(_bins, d=>d.key);
      
      all_recs.enter().append("rect")
        .attr("class", "bar")
        .merge(all_recs)
        .attr("transform", function(d){
          return("translate(" + (d.x0 + _xScaleState.bandwidth() / 1.5) + "," + (yName(d.color) + _yScaleState(d.length) - height) +")")
        })
        .attr("data-id", d=>d.color)
        .transition()
        .duration(500)
        .ease(d3.easeLinear)
        .attr("fill", d => _colorGenerator(d.color))
        .attr("width", d => _xScaleState.bandwidth() * 0.8)
        .attr("height", d => height - _yScaleState(d.length));
      
      all_recs
          .exit()
          .transition()
          .duration(500)
          .ease(d3.easeLinear)
          .attr("height", 0)
          .remove();
      
      svg_state.select('.yAxis').call(_yAxis);
      svg_state.select('.xAxis').call(_xAxisState);
      
      _yScaleState.domain([0, yScaleYearDomainMax]);
    }

    
    function compute_hist(states, state_data, histogram)
    {
      var allDensity = [];
      for (i in states){
        var state = states[i]
        var bins = histogram(state_data[state]);
        bins = d3.map(bins, function(d, j){
          d["key"] = state + j;
          d["color"] = state;
          return d;
        });
        allDensity.push({
          key: state,
          bins: bins
        });
      }
      return allDensity;
    }
    
    
    var beer_data_path = "https://raw.githubusercontent.com/kkcp-dsi/CraftBeerRatingsAnalysis/main/data/all_beers_d3.csv";
    var rowConverter = function (d) {
      return {
        state: d.state,
        beer_style: d.beer_style,
        beer_abv: +d.beer_abv,
        beer_ibu: +d.beer_ibu,
        beer_average_rating: +d.beer_average_rating,
        beer_num_ratings: +d.beer_num_ratings,
        beer_added: d.beer_added,
        year: +d.year
        }
    };
    // set the dimensions and margins of the graph
    var margin = {top: 100, right: 40, bottom: 50, left:120},
        width = 700 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;
    
     // X axis: scale and draw:
    var xScale = d3.scaleLinear()
      .domain([2.0, 5.0]) 
      .range([0, width]);
    
    var xAxis = d3.axisBottom()
      .scale(xScale);
    
    var yName = d3.scaleBand()
      .range([0, height])
      .paddingInner(1);

    var yAxis = d3.axisLeft()
      .scale(yName);

    var yScale = d3.scaleLinear()
      .domain([0.0, 10.0])
      .range([ height, 0]);
    
    var yScaleYear = d3.scaleLinear()
      .domain([0, 1000])
      .range([height, 0]);

    var myColor =  d3.scaleOrdinal()
      .range(d3.schemeSet3);
    
    var lineGenerator = d3.line()
      .curve(d3.curveBasis)
      .x(d=>xScale(d[0]))
      .y(d=>yScale(d[1]));
    
    var xScaleYear = d3.scaleTime().domain(
      [new Date("2010-01-01"), new Date("2021-01-01")]).range([0, width]);
    
    var formatDate = d3.timeFormat("%d/%m/%y");
    var xAxisYear = d3.axisBottom()
      .scale(xScaleYear)
      .tickFormat(formatDate);
    
    var histogram = d3.histogram()
      .value(d=>d)   // I need to give the vector of value
      .domain(xScaleYear.domain())  // then the domain of the graphic
      .thresholds(xScaleYear.ticks(100)); // then the numbers of bins
    
    // X axis for ABV
    var xScaleABV = d3.scaleLinear()
      .domain([0.0, 20.0]) 
      .range([0, width]);
    
    var xAxisABV = d3.axisBottom()
      .scale(xScaleABV);
    
    var yScaleABV = d3.scaleLinear()
      .domain([0.0, 4.0])
      .range([ height, 0]);
    
    var abvLineGenerator = d3.line()
      .curve(d3.curveBasis)
      .x(d=>xScaleABV(d[0]))
      .y(d=>yScaleABV(d[1]));
    
    // X axis for IBU
    var xScaleIBU = d3.scaleLinear()
      .domain([0.0, 150]) 
      .range([0, width]);
    
    var xAxisIBU = d3.axisBottom()
      .scale(xScaleIBU);
    
    var yScaleIBU = d3.scaleLinear()
      .domain([0.0, 2.0])
      .range([ height, 0]);
    
    var ibuLineGenerator = d3.line()
      .curve(d3.curveBasis)
      .x(d=>xScaleIBU(d[0]))
      .y(d=>yScaleIBU(d[1]));
      
    // X axis for state
    var xScaleState = d3.scaleBand()
      .range([0, width * 2.2]);
    
    var xAxisState = d3.axisBottom()
      .scale(xScaleState);  
      
    var yScaleState = d3.scaleLinear()
      .domain([0.0, 10000])
      .range([ height, 0]);
      
    // append the svg object to the body of the page
    var svg = create_svg(d3.select("#state_hist"), margin, height, width,  xAxis, yAxis, "Beer style average rating");
    
    // append the svg object to the body of the page
    var svg_popularity = create_svg(d3.select("#state_hist_popular"), margin, height, width,  xAxisYear, yAxis, "Beer style popularity");
    
    var svg_abv = create_svg(d3.select("#beer_abv"), margin, height, width,  xAxisABV, yAxis, "Beer style ABV");
    
    var svg_ibu = create_svg(d3.select("#beer_ibu"), margin, height, width,  xAxisIBU, yAxis, "Beer style IBU");
    
    var svg_state = create_svg(d3.select("#beer_state"), margin, height, width *  2.2,  xAxisState, yAxis, "Beer style by state");
    
    d3.csv(beer_data_path, rowConverter).then(function(data){
      var beer_style_data = {};
      var beer_style_by_state = {};
      
      for (var i in data)
      {
        var beer_style = data[i].beer_style;
        var state = data[i].state;
        
        if (!(beer_style in beer_style_data))
        {
          var beer_characteristics = {
            'beer_abv': [],
            'beer_ibu': [],
            'beer_average_rating':[],
            'beer_num_ratings':[],
            'beer_added': [],
            'year': [],
            'state': []
          }
          beer_style_data[beer_style] = beer_characteristics
        }
        
        beer_style_data[beer_style]['beer_abv'].push(data[i].beer_abv);
        beer_style_data[beer_style]['beer_ibu'].push(data[i].beer_ibu);
        beer_style_data[beer_style]['beer_average_rating'].push(data[i].beer_average_rating);
        beer_style_data[beer_style]['beer_num_ratings'].push(data[i].beer_num_ratings);
        beer_style_data[beer_style]['beer_added'].push(new Date(data[i].beer_added));
        beer_style_data[beer_style]['year'].push(data[i].year);
        
        
        if (!(beer_style in beer_style_by_state))
        {
          beer_style_by_state[beer_style] = {};
        }
        
        var translateState = data[i].state;
        if (translateState != undefined)
          translateState = getStateAbbr(data[i].state.replace('_', ' '));
        if (translateState != undefined){
          if (!(translateState in beer_style_by_state[beer_style])){
            beer_style_by_state[beer_style][translateState] = 0;
          }
          beer_style_by_state[beer_style][translateState] += 1;
        }
      }
      
      var items = Object.keys(beer_style_data).map(function(key) {
        return [key, beer_style_data[key]];
      }).sort(
        function(x, y){
          return d3.descending(x[1].beer_average_rating.length, y[1].beer_average_rating.length)
        }
      );
      
      var topItems = items.slice(0, 20);
      myColor.domain(topItems.map(d=>d[0]));
      
      var allStates = new Set(Object.keys(beer_style_by_state).map(d=>Object.keys(beer_style_by_state[d])).flat());
      
      xScaleState.domain(allStates);
      
      var mySelect = $('#states');
      $.each(topItems, function(key, val) {
          mySelect.append(
              $('<option></option>').val(val[0]).html(val[0])
          );
      });

      $('#select_all_states').change(function() {
          if(this.checked) {
            $('#states').prop('disabled', true);
            
            var topItemsRatingData = {};
            var topItemsYearDate = {};
            var topItemsBeerABV = {};
            var topItemsBeerIBU = {};
            topItems.map(d => topItemsRatingData[d[0]] = d[1].beer_average_rating);
            topItems.map(d => topItemsYearDate[d[0]] = d[1].beer_added);
            topItems.map(d => topItemsBeerABV[d[0]] = d[1].beer_abv.filter(d=>!isNaN(d)));
            topItems.map(d => topItemsBeerIBU[d[0]] = d[1].beer_ibu.filter(d=>!isNaN(d)));
            
            var beerStyleStatebins = [];
            for (i in topItems){
              var style = topItems[i][0];
              for (state in beer_style_by_state[style]){
                beerStyleStatebins.push({
                  'x0' : xScaleState(state) - xScaleState.bandwidth() / 2,
                  'x1' : xScaleState(state) + xScaleState.bandwidth() / 2,
                  'key' : style + state,
                  'color' : style,
                  'length': beer_style_by_state[style][state]
                });
              }
            }
            
            sortedDensity = compute_density(Object.keys(topItemsRatingData), topItemsRatingData, xScale.ticks(30));
            yName.domain($.map(sortedDensity, d => d.key));
            update(svg, sortedDensity, lineGenerator);
            
            bins = compute_hist(Object.keys(topItemsYearDate), topItemsYearDate, histogram)
              .map(d=>d.bins).flat();
            update_hist(svg_popularity, bins, xScaleYear, yScaleYear);
            
            sortedDensity = compute_density(Object.keys(topItemsBeerABV), topItemsBeerABV, xScaleABV.ticks(30));
            update(svg_abv, sortedDensity, abvLineGenerator);
            
            sortedDensity = compute_density(Object.keys(topItemsBeerIBU), topItemsBeerIBU, xScaleIBU.ticks(30));
            update(svg_ibu, sortedDensity, ibuLineGenerator);
            
            //Beer style by state histogram
            update_state_hist(beerStyleStatebins, svg_state, xScaleState, yScaleState, xAxisState, yAxis, myColor);
            
          }else{
             $('#states').prop('disabled', false);
             $("#states").change();
          }
      });
      
      var stateSelect = $("#states").select2({multiple: true});
      stateSelect.on("change", function (e) {
        
        var selections = $(e.currentTarget).val();
        var topItemsRatingData = {};
        var topItemsYearDate = {};
        var topItemsBeerABV = {};
        var topItemsBeerIBU = {};
        var beerStyleStatebins = [];
        for (i in selections){
          var style = selections[i];
          topItemsRatingData[style] = beer_style_data[style].beer_average_rating;
          topItemsYearDate[style] = beer_style_data[style].beer_added;
          topItemsBeerABV[style] = beer_style_data[style].beer_abv.filter(d=>!isNaN(d));
          topItemsBeerIBU[style] = beer_style_data[style].beer_ibu.filter(d=>!isNaN(d));
          
          for (state in beer_style_by_state[style]){
            beerStyleStatebins.push({
              'x0' : xScaleState(state) - xScaleState.bandwidth() / 2,
              'x1' : xScaleState(state) + xScaleState.bandwidth() / 2,
              'key' : style + state,
              'color' : style,
              'length': beer_style_by_state[style][state]
            });
          }
        }
        sortedDensity = compute_density(Object.keys(topItemsRatingData), topItemsRatingData, xScale.ticks(30));
        yName.domain($.map(sortedDensity, d => d.key));
        update(svg, sortedDensity, lineGenerator);
        
        bins = compute_hist(Object.keys(topItemsYearDate), topItemsYearDate, histogram)
          .map(d=>d.bins).flat();
        update_hist(svg_popularity, bins, xScaleYear, yScaleYear);
        
        sortedDensity = compute_density(Object.keys(topItemsBeerABV), topItemsBeerABV, xScaleABV.ticks(30));
        update(svg_abv, sortedDensity, abvLineGenerator);
        
        sortedDensity = compute_density(Object.keys(topItemsBeerIBU), topItemsBeerIBU, xScaleIBU.ticks(30));
        update(svg_ibu, sortedDensity, ibuLineGenerator);
        
        //Beer style by state histogram
        update_state_hist(beerStyleStatebins, svg_state, xScaleState, yScaleState, xAxisState, yAxis, myColor);
      });
      $("#states").change();
    });
    
    var states = {
      'Alabama': 'AL',
      'Alaska': 'AK',
      'American Samoa': 'AS',
      'Arizona': 'AZ',
      'Arkansas': 'AR',
      'California': 'CA',
      'Colorado': 'CO',
      'Connecticut': 'CT',
      'Delaware': 'DE',
      'District Of Columbia': 'DC',
      'Federated States Of Micronesia': 'FM',
      'Florida': 'FL',
      'Georgia': 'GA',
      'Guam': 'GU',
      'Hawaii': 'HI',
      'Idaho': 'ID',
      'Illinois': 'IL',
      'Indiana': 'IN',
      'Iowa': 'IA',
      'Kansas': 'KS',
      'Kentucky': 'KY',
      'Louisiana': 'LA',
      'Maine': 'ME',
      'Marshall Islands': 'MH',
      'Maryland': 'MD',
      'Massachusetts': 'MA',
      'Michigan': 'MI',
      'Minnesota': 'MN',
      'Mississippi': 'MS',
      'Missouri': 'MO',
      'Montana': 'MT',
      'Nebraska': 'NE',
      'Nevada': 'NV',
      'New Hampshire': 'NH',
      'New Jersey': 'NJ',
      'New Mexico': 'NM',
      'New York': 'NY',
      'North Carolina': 'NC',
      'North Dakota': 'ND',
      'Northern Mariana Islands': 'MP',
      'Ohio': 'OH',
      'Oklahoma': 'OK',
      'Oregon': 'OR',
      'Palau': 'PW',
      'Pennsylvania': 'PA',
      'Puerto Rico': 'PR',
      'Rhode Island': 'RI',
      'South Carolina': 'SC',
      'South Dakota': 'SD',
      'Tennessee': 'TN',
      'Texas': 'TX',
      'Utah': 'UT',
      'Vermont': 'VT',
      'Virgin Islands': 'VI',
      'Virginia': 'VA',
      'Washington': 'WA',
      'West Virginia': 'WV',
      'Wisconsin': 'WI',
      'Wyoming': 'WY'
    }
    
    function getStateAbbr(name) {
      return states[name];
    }