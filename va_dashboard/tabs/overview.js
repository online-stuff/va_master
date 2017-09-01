var React = require('react');
var connect = require('react-redux').connect;
var Network = require('../network');
var Chart = require("react-chartjs-2").Chart;
var DoughnutChart = require("react-chartjs-2").Doughnut;
var BarChart = require("react-chartjs-2").Bar;
var defaults = require("react-chartjs-2").defaults;
var Bootstrap = require('react-bootstrap');
var joint = require('jointjs');
var ReactDOM = require('react-dom');

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
        return {providers: [], loading: true, index: 0};
    },
    componentWillMount() {
        this.getHosts();
    },
    getHosts: function(){
        var data = {providers: []};
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
        var HostRowsRedux = connect(function(state){
            return {auth: state.auth};
        })(HostRows);
        var LogRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        }, null, null, { withRef: true })(Log);
        var diagram = [];
        var provider_rows = this.state.providers.map(function(provider) {
            var provider_servers = provider.servers.map(function(i) {
                return {name: i.provider_name, ip: i.ip};
            });
            diagram.push({name: provider.provider_name, servers: provider_servers});
            return {provider_name: provider.provider_name, servers: provider.servers, provider_usage: provider.provider_usage};
        }.bind(this));
        const spinnerStyle = {
            top: '30%',
            display: this.state.loading ? "block": "none",
        };
        var provider_redux = null;
        if(this.state.providers.length > 0){
            provider_redux = <HostRowsRedux providers={provider_rows} />;
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

var conf = {
    style: [{
        selector: 'node',
        style: {
            shape: 'hexagon',
            'background-color': 'red'
        }
    }],
    elements: [
        { data: { id: 'a' } },
        { data: { id: 'b' } },
        {
            data: {
            id: 'ab',
            source: 'a',
            target: 'b'
            }
    }]
};

var Jointjs = React.createClass({
    getInitialState: function () {
        this.graph = new joint.dia.Graph();
        return {};
    },
    changeDiagram: function (props){
        var scale = 1;
        if(props.length > 2){
            scale = 0.8;
            this.paper.scale(scale);
        }
        var root_x = this.width/scale/2 - 75, root_y = this.height/scale/2 - 15;
        var root_rect = new joint.shapes.basic.Rect({
            position: { x: root_x, y: root_y},
            size: { width: 100, height: 30 },
            attrs: {
                rect: { fill: '#337ab7', rx: '10', ry: '10' },
                text: { text: "va-master", fill: 'white' }
            }
        });
        var rect = [root_rect], links = [], h_trans = [{x: root_x+120, y: root_y}, {x: root_x-120, y: root_y}, {x: root_x, y: root_y-50}, {x: root_x, y: root_y+50}, {x: root_x-150, y: root_y-50}, {x: root_x-150, y: root_y+50}, {x: root_x+150, y: root_y-50}, {x: root_x+150, y: root_y+50}];
        var i_trans = [
            [{x: 130, y: 45}, {x: 130, y: -45}, {x: 130, y: 0}, {x: 0, y: 45}, {x: 0, y: -45}, {x: -130, y: 45}, {x: -130, y: -45}],
            [{x: -130, y: 45}, {x: -130, y: -45}, {x: -130, y: 0}, {x: 0, y: 45}, {x: 0, y: -45}, {x: 130, y: 45}, {x: 130, y: -45}],
            [{x: -130, y: -45}, {x: 130, y: -45}, {x: 0, y: -45}, {x: -130, y: 0}, {x: 130, y: 0}, {x: -130, y: 45}, {x: 130, y: 45}],
            [{x: -130, y: 45}, {x: 130, y: 45}, {x: 0, y: 45}, {x: -130, y: 0}, {x: 130, y: 0}, {x: -130, y: -45}, {x: 130, y: -45}]
        ];
        for(var i=0; i<props.length; i++){
            var provider = props[i];
            var h_index = rect.length;
            var txt = provider.name;
            txt = txt.length > 17 ? txt.substring(0,17) : txt;
            var width = txt.length > 12 ? 120 : 100;
            rect.push(new joint.shapes.basic.Rect({
                position: h_trans[i],
                size: { width: width, height: 30 },
                attrs: {
                    rect: { fill: 'gray', rx: '10', ry: '10' },
                    text: { text: txt, fill: 'white' }
                }
            }));

            links.push(new joint.dia.Link({
                source: { id: rect[0].id },
                target: { id: rect[h_index].id }
            }));

            for(var j=0; j<provider.servers.length; j++){
                rect.push(new joint.shapes.basic.Rect({
                    position: h_trans[i],
                    size: { width: 120, height: 40 },
                    attrs: {
                        rect: { fill: 'green', rx: '10', ry: '10' },
                        text: { text: provider.servers[j].name + "\nIP: " + provider.servers[j].ip , fill: 'white' }
                    }
                }));
                //link between provider and server
                rect[rect.length-1].translate(i_trans[i][j].x, i_trans[i][j].y);

                links.push(new joint.dia.Link({
                    source: { id: rect[h_index].id },
                    target: { id: rect[rect.length-1].id }
                }));
            }
        }
        this.graph.addCells(rect.concat(links));
    },
    componentDidMount(){
        this.width = ReactDOM.findDOMNode(this.refs.diagram).parentNode.offsetWidth - 31;
        this.height = 200;
        this.paper = new joint.dia.Paper({
            el: this.refs.diagram,
            width: this.width,
            height: this.height,
            model: this.graph,
            gridSize: 1,
            interactive: false
        });
        this.changeDiagram(this.props.data);
    },
    shouldComponentUpdate(){
        return false;
    },
    componentWillReceiveProps(nextProps){
        if (nextProps.data !== this.props.data) {
            this.graph.clear();
            this.changeDiagram(nextProps.data);
        }
    },
    componentWillUnmount(){
        this.graph.clear();
        this.paper.remove();
    },
    getGraph(){
        return this.graph;
    },
    getPaper(){
        return this.paper;
    },
    render(){
        return <div ref="diagram" />
    }
});

var Diagram = React.createClass({
    getInitialState: function () {
        return {providers: [], loading: true};
    },
    componentWillMount() {
        // this.getDiagram();
        // var me = this;
        // var data = [{
        //     name: "Libvirt",
        //     servers: [
        //         {name: "va-backup"},
        //         {name: "va-email"},
        //         {name: "va-monitoring"},
        //     ]
        // }];
        // setTimeout(function(){ me.setState({providers: data}); }, 5000);
    },
    // getDiagram: function(){
    //     var data = {providers: []};
    //     var me = this;
    //     Network.post('/api/providers/diagram', this.props.auth.token, data).done(function(data) {
    //         me.setState({providers: data, loading: false});
    //     }).fail(function (msg) {
    //         me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
    //     });
    // },
    render: function() {
        // const spinnerStyle = {
        //     display: this.state.loading ? "block": "none",
        // };
        return (
            <Bootstrap.Panel ref="panel" header="Diagram" bsStyle='primary'>
                <Jointjs ref="graph" data={this.props.providers} />
            </Bootstrap.Panel>);
    }
});

var Host = React.createClass({
    getInitialState: function () {
        var cpuData = [], ramData = [], diskData = [], cost = 0, e_cost = 0;
        var servers = this.props.chartData.map(function(server) {
            cpuData.push(server.used_cpu);
            ramData.push(server.used_ram);
            diskData.push(server.used_disk);
            cost += server.month_to_date;
            e_cost += server.monthly_estimate;
            return server.provider_name;
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

var HostRows = React.createClass({
    getInitialState: function () {
        return {index: 0};
    },
    nextHost: function () {
        if(this.state.index < this.props.providers.length-1)
            this.setState({index: this.state.index + 1});
    },
    prevHost: function () {
        if(this.state.index > 0)
            this.setState({index: this.state.index - 1});
    },
    render: function() {
        var HostRedux = connect(function(state){
            return {auth: state.auth};
        })(Host);
        var provider = this.props.providers[this.state.index];
        return (
            <Bootstrap.Panel header={provider.provider_name + " / Instances: " + provider.servers.length} bsStyle='primary' className="provider-billing-block">
                <Bootstrap.Glyphicon glyph='arrow-left' onClick={this.prevHost}></Bootstrap.Glyphicon>
                <HostRedux key={provider.provider_name} title={provider.provider_name} chartData={provider.servers} provider_usage={provider.provider_usage} />
                <Bootstrap.Glyphicon glyph='arrow-right' onClick={this.nextHost}></Bootstrap.Glyphicon>
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
        var provider = window.location.provider;
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
