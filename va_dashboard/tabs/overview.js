var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Chart = require("react-chartjs-2").Chart;
var DoughnutChart = require("react-chartjs-2").Doughnut;
var BarChart = require("react-chartjs-2").Bar;
var defaults = require("react-chartjs-2").defaults;
var Bootstrap = require('react-bootstrap');
var ReactDOM = require('react-dom');
var Graph = require('react-graph-vis').default;

Chart.pluginService.register({
    beforeDraw: function(chart) {
        if(chart.config.type === "doughnut"){
            var width = chart.chart.width,
                height = chart.chart.height,
                ctx = chart.chart.ctx;

            ctx.restore();
            var fontSize = (height / 114).toFixed(2);

            var allData = chart.data.datasets[0].data;
            if(chart.config.options.rotation == Math.PI){
                var total = 0;
                for (var i in allData) {
                    if(!isNaN(allData[i]))
                        total += allData[i];
                }
                if(isNaN(allData[allData.length-1])){
                    unit = "";
                    if(chart.titleBlock.options.text == "MEMORY"){
                        unit = " GB";
                    }else if(chart.titleBlock.options.text == "STORAGE"){
                        unit = " GB";
                    }
                    text = total.toString() + unit;
                }else{
                    var percentage = Math.round(((total - allData[allData.length-1]) / total) * 100);
                    text = percentage.toString() + "%";
                }

                var textX = Math.round((width - ctx.measureText(text).width) / 2),
                    textY = height / 1.2;
            }else{
                fontSize = (height / 114).toFixed(2);
                if(!allData[0])
                    allData[0] = 0
                if(chart.titleBlock.options.text == "MEMORY"){
                    text = chart.config.options.customInnerData + " GB";
                }else if(chart.titleBlock.options.text == "USERS"){
                    text = allData[0] + "/" + allData[1];
                }else{
                    text = chart.config.options.customInnerData;
                }

                var textX = Math.round((width - ctx.measureText(text).width) / 2),
                    textY = height / 1.5;
            }
            ctx.font = fontSize + "em sans-serif";
            ctx.textBaseline = "middle";

            ctx.fillText(text, textX, textY);
            ctx.save();
        }
    }
});

var Overview = React.createClass({
    getInitialState: function () {
        defaults.global.legend.display = false;
        return {providers: {}, loading: true, index: 0};
    },
    componentWillMount() {
        this.getProviders();
    },
    getProviders: function(){
        var data = {providers: [], sort_by_location: true};
        var me = this;
        Network.post('/api/providers/info', this.props.auth.token, data).done(function(data) {
            me.setState({providers: data, loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentWillUnmount: function () {
        this.refs.log.getWrappedInstance().close_socket();
    },
    render: function() {
        var ProviderRowsRedux = connect(function(state){
            return {auth: state.auth};
        })(ProviderRows);
        var LogRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(Log);
        var diagram = {}, provider_rows = [];
        for(var loc in this.state.providers) {
            diagram[loc] = [];
        }
        for(var loc in this.state.providers) {
            var provider = this.state.providers[loc];
            for(var key=0; key < provider.length; key++){
                var pp = provider[key], provider_servers = [];
                for(var kkey=0; kkey < pp.servers.length; kkey++) {
                    var ii = pp.servers[kkey];
                    provider_servers.push( {name: ii.hostname, ip: ii.ip} );
                }
                diagram[loc].push({name: pp.provider_name, servers: provider_servers});
                provider_rows.push({name: pp.provider_name, servers: pp.servers, provider_usage: pp.provider_usage});
            }
        }
        const spinnerStyle = {
            top: '30%',
            display: this.state.loading ? "block": "none",
        };
        var provider_redux = null;
        if(provider_rows.length > 0){
            provider_redux = <ProviderRowsRedux providers={provider_rows} />;
        }
        return (
            <div>
                <Diagram providers={diagram} />
                <div className="graph-block">
                    <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
                    {provider_redux}
                </div>
                <LogRedux ref="log" />
            </div>);
    }
});

var Diagram = React.createClass({
    getInitialState: function () {
        return {
            providers: [], 
            loading: true, 
            width: "", 
            options: {
                layout: {
                    hierarchical: {
                        direction: "UD", 
                        sortMethod: "directed",
                        //nodeSpacing: 60,
                        levelSeparation: 50
                    }
                },
                edges: {
                    color: "#000000"
                },
                nodes: {
                    size: 15,
                    font: {
                        size : 12,
                        color : '#ffffff'
                    }
                },
		physics: {
		    enabled: false
		}
            }
        };
    },
    render: function() {
        var graph = {nodes: [], edges: []}, ll = 0;
        graph.nodes.push({id: 'master', label: "va-master", shape: 'box'});
        for(var location in this.props.providers){
            var provider = this.props.providers[location];
            var txt = location;
            txt = txt.length > 17 ? txt.substring(0,17) : txt;
            graph.nodes.push({id: location, label: txt, shape: 'box'});
            graph.edges.push({from: 'master', to: location});
            ll++;

            for(var i=0; i<provider.length; i++){
                var p = provider[i];
                var txt = p.name, id = location + i;
                txt = txt.length > 17 ? txt.substring(0,17) : txt;

                graph.nodes.push({id: id, label: txt, shape: 'box', color: 'gray'});
                graph.edges.push({from: location, to: id});

                for(var j=0; j<p.servers.length; j++){
                    var server = p.servers[j];
                    var txt = server.name + "\nIP: " + server.ip, newId = id + "/" + j;
                    graph.nodes.push({id: newId, label: txt, shape: 'box', color: 'green'});
                    graph.edges.push({from: id, to: newId});
                }
            }
        }
        var style = { width: '100%', height: '200px' };
        return (
            <Bootstrap.Panel ref="panel" header="Diagram" bsStyle='primary'>
                <Graph graph={graph} options={this.state.options} style={style} events={{}} />
            </Bootstrap.Panel>);
    }
});

var Provider = React.createClass({
    getInitialState: function () {
        var cpuData = [], ramData = [], diskData = [], cost = 0, e_cost = 0;
        var servers = this.props.chartData.map(function(server) {
            cpuData.push(server.used_cpu);
            ramData.push(server.used_ram);
            diskData.push(server.used_disk);
            cost += server.month_to_date;
            e_cost += server.monthly_estimate;
            return server.hostname;
        });
        servers.push("Free");
        var usage = this.props.provider_usage;
        cpuData.push(usage.free_cpus);
        ramData.push(usage.free_ram);
        diskData.push(usage.free_disk);
        var data = [cpuData, ramData, diskData];
        var colors = this.getRandomColors(servers.length+1);
        return {
            chartData: data,
            labels: servers,
            colors: colors,
            cost: cost,
            e_cost: e_cost
        };
    },

    getRandomColors: function(count) {
        var letters = '0123456789ABCDEF'.split('');
        var colors = [];
        for(var j = 0; j < count; j++){
            var color = '#';
            for (var i = 0; i < 6; i++ ) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            colors.push(color);
        }
        return colors;
    },
    render: function() {
        var DoughnutRedux = connect(function(state){
            return {auth: state.auth};
        })(DoughnutComponent);
        var cost = this.state.cost, e_cost = this.state.e_cost;
        if(!isNaN(cost)){
            cost = Math.round(cost);
        }
        if(!isNaN(e_cost)){
            e_cost = Math.round(e_cost);
        }
        return (
            <div id="billing-panel-content">
                <DoughnutRedux data={this.state.chartData[0]} labels={this.state.labels} colors={this.state.colors} title="CPU" />
                <DoughnutRedux data={this.state.chartData[1]} labels={this.state.labels} colors={this.state.colors} title="MEMORY"  />
                <DoughnutRedux data={this.state.chartData[2]} labels={this.state.labels} colors={this.state.colors} title="STORAGE"  />
                <div className="billing-info">
                    <div>
                        <div className="provider-billing">{cost}</div>
                        <div>Current monthly cost</div>
                    </div>
                    <div>
                        <div className="provider-billing">{e_cost}</div>
                        <div>Monthly estimated cost</div>
                    </div>
                </div>
            </div>
        );
    }
});

var ProviderRows = React.createClass({
    getInitialState: function () {
        return {index: 0};
    },
    nextProvider: function () {
        if(this.state.index < this.props.providers.length-1)
            this.setState({index: this.state.index + 1});
    },
    prevProvider: function () {
        if(this.state.index > 0)
            this.setState({index: this.state.index - 1});
    },
    render: function() {
        var ProviderRedux = connect(function(state){
            return {auth: state.auth};
        })(Provider);
        var provider = this.props.providers[this.state.index];
        return (
            <Bootstrap.Panel header={provider.name + " / Instances: " + provider.servers.length} bsStyle='primary' className="provider-billing-block">
                <Bootstrap.Glyphicon glyph='arrow-left' onClick={this.prevProvider}></Bootstrap.Glyphicon>
                <ProviderRedux key={provider.name} title={provider.name} chartData={provider.servers} provider_usage={provider.provider_usage} />
                <Bootstrap.Glyphicon glyph='arrow-right' onClick={this.nextProvider}></Bootstrap.Glyphicon>
            </Bootstrap.Panel>
        );
    }
});

var DoughnutComponent = React.createClass({
    getInitialState: function () {
        return {chartOptions: {
                    maintainAspectRatio: false, title: {
                        display: true,
                        text: this.props.title
                    },
                    cutoutPercentage: 70,
                    rotation: 1 * Math.PI,
                    circumference: 1 * Math.PI
                }, chartData: {
                    labels: this.props.labels,
                    datasets: [
                        {
                            data: this.props.data,
                            backgroundColor: this.props.colors,
                            hoverBackgroundColor: this.props.colors
                        }]
                }};
            },
    render: function() {
        return (
            <div className="chart">
                <DoughnutChart data={this.state.chartData} options={this.state.chartOptions}/>
            </div>
        );
    }
});

var Log = React.createClass({
    getInitialState: function () {
        return {logs: [], category: ['info', 'warning', 'danger'] }
    },
    initLog: function () {
        var provider = window.location.host;
        if(provider.indexOf(":") == 0){
            provider += ":80";
        }
        var protocol =  window.location.protocol === "https:" ? "wss" : "ws";
        this.ws = new WebSocket(protocol  +"://"+ provider +"/log");
        var me = this;
        this.ws.onmessage = function (evt) {
            var data = JSON.parse(evt.data);
            var logs = [];
            if(data.type === "update")
                logs = me.state.logs.concat([data.message]);
            else if(data.type === "init")
                logs = data.logs.reverse();
            me.setState({logs: logs});
        };
        this.ws.onerror = function(evt){
            me.ws.close();
            me.props.dispatch({type: 'SHOW_ALERT', msg: "Socket error."});
        };
    },
    componentDidMount: function () {
        if(!this.props.alert.show)
            this.initLog();
    },
    close_socket: function () {
        this.ws.close();
    },
    render: function() {
        var times = [], currentDate = new Date(); //"2017-02-21T14:00:14+00:00"
        var prevHourTs = currentDate.setHours(currentDate.getHours()-1);
        var logs = this.state.logs;
        var datasets = [{
            label: 'info',
            data: [],
            backgroundColor: "#31708f",
            borderColor: "#31708f"
        }, {
            label: 'warning',
            data: [],
            backgroundColor: "#ffa726",
            borderColor: "#ffa726"
        }, {
            label: 'danger',
            data: [],
            backgroundColor: "#a94442",
            borderColor: "#a94442"
        }];
        if(logs.length > 0){
            var prev_log = logs[0];
        }
        var logs_limit = 3, brojac=0, log_rows = [];
        for(var i=0; i<logs.length; i++){
            log = logs[i];
            var logClass = log.severity == "warning" ? "text-warning" : (log.severity == "err" || log.severity == "critical" || log.severity == "emergency") ? "text-danger" : "text-info";
            var timestamp = new Date(log.timestamp);
            if(timestamp.getTime() > prevHourTs){
                var logLabel = logClass.split('-')[1];
                var prevTimestamp = new Date(prev_log.timestamp);
                var category = this.state.category;
                // groups logs with same hh:mm for the graph
                if(i > 0 && timestamp.getHours() == prevTimestamp.getHours() && timestamp.getMinutes() == prevTimestamp.getMinutes()){
                    var index = category.indexOf(logLabel);
                    datasets[index].data[datasets[index].data.length - 1] += 1;
                }else{
                    times.push(timestamp);
                    for(j=0; j<category.length; j++){
                        if(category[j] == logLabel){
                            datasets[j].data.push(1);
                        }else{
                            datasets[j].data.push(0);
                        }
                    }
                }
                if(i > 0){
                    prev_log = log;
                }
            }
            if(brojac < logs_limit){
            var hour = timestamp.getHours();
            var min = timestamp.getMinutes();
            var sec = timestamp.getSeconds();
            var message = JSON.parse(log.message), msg = "";
            for(var key in message){
                if(typeof message[key] === 'object'){
                    msg += message[key].method + " ";
                }else{
                    msg += message[key] + " ";
                }
            }
            log_rows.push (
                <div key={i} className={"logs " + logClass}>{timestamp.toISOString().slice(0, 10) + " " + hour + ":" + min + ":" + sec + ", " + message.user + ", " + log.provider + ", " + log.severity + ", " + message.path + ", " + msg}</div>
            );
            }
            brojac++;
        }
        var LogChartRedux = connect(function(state){
            return {auth: state.auth};
        })(LogChart);
        return (
            <Bootstrap.Panel header='Logs' bsStyle='primary' className="log-block">
                <LogChartRedux datasets={datasets} labels={times} minDate={currentDate} />
                {log_rows}
            </Bootstrap.Panel>
        );
    }
});

var LogChart = React.createClass({
    getInitialState: function () {
        var maxDate = new Date();
        var maxDateTs = maxDate.setMinutes(maxDate.getMinutes() + 1);
        return {chartOptions: {
                    maintainAspectRatio: false,
                    responsive: true,
                    scales: {
                        xAxes: [{
                            type: 'time',
                            stacked: true,
                            display: false,
                            //categoryPercentage: 1.0,
                            //barPercentage: 1.0,
                            time: {
                                displayFormats: {
                                    minute: 'HH:mm',
                                    hour: 'HH:mm',
                                    second: 'HH:mm:ss',
                                },
                                tooltipFormat: 'DD/MM/YYYY HH:mm',
                                unit: 'minute',
                                unitStepSize: 0.5,
                                min: this.props.minDate,
                                max: maxDateTs
                            },
                            gridLines: {
                                display:false
                            }
                        }],
                        yAxes: [{
                            display: false,
                            stacked: true,
                            gridLines: {
                                display:false
                            }
                        }]
                    }
                }, chartData: {
                    labels: this.props.labels,
                    datasets: this.props.datasets
                }};
    },
    componentDidMount: function () {
        var me = this;
        this.intervalId = setInterval(function(){
            var chartOptions = me.state.chartOptions;
            var mindate = new Date(chartOptions.scales.xAxes[0].time.min);
            var maxdate = new Date(chartOptions.scales.xAxes[0].time.max);
            mindate.setMinutes(mindate.getMinutes() + 1);
            maxdate.setMinutes(maxdate.getMinutes() + 1);
            chartOptions.scales.xAxes[0].time.min = mindate;
            chartOptions.scales.xAxes[0].time.max = maxdate;
            me.setState({chartOptions: chartOptions});
        }, 60000);
    },
    componentWillUnmount: function() {
        clearInterval(this.intervalId);
    },
    render: function() {
        return (
            <div className="log-chart">
                <BarChart data={this.state.chartData} options={this.state.chartOptions} redraw />
            </div>
        );
    }
});

Overview = connect(function(state) {
    return {auth: state.auth, alert: state.alert};
})(Overview);

module.exports = Overview;
