import React, { Component } from 'react';
import {connect} from 'react-redux';
import {Chart, Doughnut, Bar, defaults} from "react-chartjs-2";
import {Glyphicon} from 'react-bootstrap';
import Graph from'react-graph-vis';
var Network = require('../network');
import {getRandomColors} from './util'; 

Chart.defaults.global.defaultFontFamily = 'Ubuntu';
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
                    text = allData[0] + "+" + allData[1];
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

class Overview extends Component {
    constructor (props) {
        super(props)
        defaults.global.legend.display = false;
        this.state = {providers: {}, loading: true};
        this.initLog = this.initLog.bind(this);
        this.getProviders = this.getProviders.bind(this);
    }
    initLog() {
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
                me.props.dispatch({type: 'UDDATE_LOGS', logs: data.message});
            else if(data.type === "init")
                me.props.dispatch({type: 'INIT_LOGS', logs: data.logs.reverse()});
        };
        this.ws.onerror = function(evt){
            me.ws.close();
            me.props.dispatch({type: 'SHOW_ALERT', msg: "Socket error."});
        };
    }
    componentDidMount() {
        this.initLog();
        this.getProviders();
    }
    getProviders(){
        var data = {providers: [], sort_by_location: true};
        var me = this;
        Network.post('/api/providers/info', this.props.auth.token, data).done(function(data) {
            me.setState({providers: data, loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
    componentWillUnmount() {
        this.ws.close();
        this.props.dispatch({type: 'RESET_LOGS'});
    }
    render() {
        var DiagramRedux = connect(function(state){
            return {auth: state.auth, sidebar: state.sidebar};
        })(Diagram);
        var LogRedux = connect(function(state){
            return {auth: state.auth, logs: state.logs};
        })(Log);
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
                if(pp.provider_name)
                    provider_rows.push({name: pp.provider_name, servers: pp.servers, provider_usage: pp.provider_usage});
            }
        }
        const spinnerStyle = {
            top: '30%',
            display: this.state.loading ? "block": "none",
        };
        var provider_redux = null;
        if(provider_rows.length > 0){
            provider_redux = <ProviderRows providers={provider_rows} />;
        }
        return (
            <div>
                <DiagramRedux providers={diagram} />
                <div className="graph-block">
                    <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
                    {provider_redux}
                </div>
                <LogRedux />
            </div>);
    }
}

const Diagram = (props) => {
    const graphOptions = {
        layout: {
            hierarchical: {
                direction: "UD", 
                sortMethod: "directed",
                nodeSpacing: 120,
                levelSeparation: 50
            }
        },
        edges: {
            color: "#000000",
            arrows: {
                to: {
                    enabled: false,
                    scaleFactor: 0.5
                }
            }
        },
        nodes: {
            size: 15,
            font: {
                size : 11,
                color : 'white',
                face : 'Ubuntu'
            },
            margin: {
                top: 8,
                right: 8,
                left: 8,
                bottom: 8
            }
        },
        physics: {
            enabled: false,
        }
    };
    var graph = {nodes: [], edges: []}, ll = 0;
    graph.nodes.push({id: 'master', label: "va-master", shape: 'box', color: '#337ab7'});
    for(var location in props.providers){
        var provider = props.providers[location];
        var txt = location;
        txt = txt.length > 17 ? txt.substring(0,17) : txt;
        graph.nodes.push({id: location, label: txt, shape: 'box', color: '#97c2fc'});
        graph.edges.push({from: 'master', to: location});
        ll++;

        for(var i=0; i<provider.length; i++){
            var p = provider[i], txt = p.name, id = location + "/" + txt;
            if(txt){
                txt = txt.length > 17 ? txt.substring(0,17) : txt;
                graph.nodes.push({id: id, label: txt, shape: 'box', color: {border: '#696969', background: 'gray', highlight: {border: 'gray', background: '#909090'}}});
                graph.edges.push({from: location, to: id});
            }else{
                id = location;
            }

            for(var j=0; j<p.servers.length; j++){
                var server = p.servers[j];
                var txt = server.name + "\nIP: " + server.ip, newId = id + "/" + server.name;
                graph.nodes.push({id: newId, label: txt, shape: 'box', color: '#4bae4f'});
                graph.edges.push({from: id, to: newId});
            }
        }
    }
    var style = { width: '100%', height: '180px' };
    return (
        <div className="card panel-default custom-panel" style={{marginBottom: '0px'}}>
            <div className="panel-heading">Diagram</div>
            <div className="panel-body">
                <Graph graph={graph} options={graphOptions} style={style} events={{}} />
                <div className="hidden">{props.sidebar.collapsed}</div>
            </div>
        </div>
    );
}

const Provider = (props) => {
    var cpuData = [], ramData = [], diskData = [], cost = 0, e_cost = 0;
    var labels = props.chartData.map((server) => {
        cpuData.push(server.used_cpu);
        ramData.push(server.used_ram);
        diskData.push(server.used_disk);
        cost += server.month_to_date;
        e_cost += server.monthly_estimate;
        return server.hostname;
    });
    labels.push("Free");
    var usage = props.provider_usage;
    cpuData.push(usage.free_cpus);
    ramData.push(usage.free_ram);
    diskData.push(usage.free_disk);
    var chartData = [cpuData, ramData, diskData];
    var colors = getRandomColors(labels.length+1);

    var DoughnutRedux = connect(function(state){
        return {auth: state.auth};
    })(DoughnutComponent);
    if(!isNaN(cost)){
        cost = Math.round(cost);
    }
    if(!isNaN(e_cost)){
        e_cost = Math.round(e_cost);
    }
    return (
        <div id="billing-panel-content">
            <DoughnutRedux data={chartData[0]} labels={labels} colors={colors} title="CPU" />
            <DoughnutRedux data={chartData[1]} labels={labels} colors={colors} title="MEMORY"  />
            <DoughnutRedux data={chartData[2]} labels={labels} colors={colors} title="STORAGE"  />
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

class ProviderRows extends Component {
    constructor (props) {
        super(props);
        this.state = {index: 0};
        this.nextProvider = this.nextProvider.bind(this);
        this.prevProvider = this.prevProvider.bind(this);
    }
    nextProvider() {
        if(this.state.index < this.props.providers.length-1)
            this.setState({index: this.state.index + 1});
    }
    prevProvider() {
        if(this.state.index > 0)
            this.setState({index: this.state.index - 1});
    }
    render() {
        var provider = this.props.providers[this.state.index];
        return (
            <div className="provider-billing-block card panel-default custom-panel" style={{marginBottom: '0px'}}>
                <div className="panel-heading">{provider.name + " / Instances: " + provider.servers.length}</div>
                <div className="panel-body">
                    <Glyphicon glyph='arrow-left' onClick={this.prevProvider}></Glyphicon>
                    <Provider key={provider.name} title={provider.name} chartData={provider.servers} provider_usage={provider.provider_usage} />
                    <Glyphicon glyph='arrow-right' onClick={this.nextProvider}></Glyphicon>
                </div>
            </div>
        );
    }
}

const DoughnutComponent = (props) => {
    const chartOptions = {
        maintainAspectRatio: false, title: {
            display: true,
            text: props.title
        },
        cutoutPercentage: 70,
        rotation: 1 * Math.PI,
        circumference: 1 * Math.PI
    }, chartData = {
        labels: props.labels,
        datasets: [
            {
                data: props.data,
                backgroundColor: props.colors,
                hoverBackgroundColor: props.colors
            }
        ]
    };
    return (
        <div className="chart">
            <Doughnut data={chartData} options={chartOptions}/>
        </div>
    );
}

const Log = (props) => {
    var category = ['info', 'warning', 'danger'];
    var times = [], currentDate = new Date();
    var prevHourTs = currentDate.setHours(currentDate.getHours()-1);
    var logs = props.logs;
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
        var log = logs[i];
        var logClass = log.severity == "warning" ? "text-warning" : (log.severity == "err" || log.severity == "critical" || log.severity == "emergency") ? "text-danger" : "text-info";
        var timestamp = new Date(log.timestamp);
        if(timestamp.getTime() > prevHourTs){
            var logLabel = logClass.split('-')[1];
            var prevTimestamp = new Date(prev_log.timestamp);
            // groups logs with same hh:mm for the graph
            if(i > 0 && timestamp.getHours() == prevTimestamp.getHours() && timestamp.getMinutes() == prevTimestamp.getMinutes()){
                var index = category.indexOf(logLabel);
                datasets[index].data[datasets[index].data.length - 1] += 1;
            }else{
                times.push(timestamp);
                for(var j=0; j<category.length; j++){
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
        var message = log.message;
        if(brojac < logs_limit){
            var hour = timestamp.getHours();
            var min = timestamp.getMinutes();
            var sec = timestamp.getSeconds();
            try {
                message = JSON.parse(message);
                var msg = "";
                for(var key in message){
                    if(typeof message[key] === 'object'){
                        msg += message[key].method + " ";
                    }else{
                        msg += message[key] + " ";
                    }
                }
                message = timestamp.toISOString().slice(0, 10) + " " + hour + ":" + min + ":" + sec + ", " + message.user + ", " + log.provider + ", " + log.severity + ", " + message.path + ", " + msg;
            } catch(err) {}
        log_rows.push (
            <div key={i} className={"logs " + logClass}>{message}</div>
        );
        }
        brojac++;
    }
    return (
        <div className="log-block card panel-default custom-panel" style={{marginBottom: '0px'}}>
            <div className="panel-heading">Logs</div>
            <div className="panel-body">
                <LogChart datasets={datasets} labels={times} minDate={currentDate} />
                {log_rows}
            </div>
        </div>
    );
}

class LogChart extends Component {
    constructor(props) {
        super(props);
        var maxDate = new Date();
        var maxDateTs = maxDate.setMinutes(maxDate.getMinutes() + 1);
        this.state = {chartOptions: {
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
            labels: props.labels,
            datasets: props.datasets
        }};
    }
    componentDidMount() {
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
    }
    componentWillUnmount() {
        this.intervalId && clearInterval(this.intervalId);
        this.intervalId = false;
    }
    render() {
        return (
            <div className="log-chart">
                <Bar data={this.state.chartData} options={this.state.chartOptions} redraw />
            </div>
        );
    }
}

Overview = connect(function(state) {
    return {auth: state.auth};
})(Overview);

module.exports = Overview;
