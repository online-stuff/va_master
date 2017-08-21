var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var DatePicker = require('react-datepicker').default;
var moment = require('moment');
var Reactable = require('reactable');

var Log = React.createClass({
    getInitialState: function () {
        var checked = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"];
        return {
            logs: [],
            value: "",
            checked: checked
        }
    },
    initLog: function () {
        var host = window.location.host;
        if(host.indexOf(":") == 0){
            host += ":80";
        }
        var protocol =  window.location.protocol === "https:" ? "wss" : "ws";
        this.ws = new WebSocket(protocol  +"://"+ host +"/log");
        var me = this;
        this.ws.onmessage = function (evt) {
            var data = JSON.parse(evt.data);
            var logs = [];
            if(data.type === "update")
                logs = me.state.logs.concat([data.message]);
            else if(data.type === "init")
                logs = data.logs;
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
    filter: function (evt) {
        this.setState({value: evt.target.value});
    },
    updateLogs: function(startDate, endDate){
        var msg = {
            from_date: startDate,
            to_date: endDate
        };
        this.ws.send(JSON.stringify(msg));
    },
    changeTable: function(checked){
        this.setState({checked: checked});
    },
    render: function () {
        var TableRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Table);
        var DateRangeRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(DateRange);
        var me = this;
        var logs = this.state.logs.filter(function(l){
            if(me.state.checked.indexOf(l.severity) > -1) return true;
            return false;
        });
        return (
            <div id="log-page">
            	<div>
                    <DateRange updateLogs={this.updateLogs} />
                    <input type='text' placeholder='Search...' value={this.state.value} onChange={this.filter} style={{float: 'right'}}/>
	    		</div>
                <FilterBtns changeTable={this.changeTable} />
            	<TableRedux logs={logs} filterBy={this.state.value} checked={this.state.checked}/>
            </div>
	);
    }
});

var DateRange = React.createClass({
    getInitialState: function () {
        return {
            startDate: moment().subtract(1, 'days'),
            endDate: moment()
        }
    },
    handleChangeStart: function(date) {
        this.setState({
            startDate: date
        });
    },

    handleChangeEnd: function(date) {
        this.setState({
            endDate: date
        });
    },
    btnClick: function(){
        this.props.updateLogs(this.state.startDate.format('YYYY-MM-DD'), this.state.endDate.format('YYYY-MM-DD'));
    },
    render: function () {
        return (
            <div className="date-range">
                From: 
                <DatePicker
                    dateFormat="DD/MM/YYYY"
                    selected={this.state.startDate}
                    selectsStart
                    startDate={this.state.startDate}
                    endDate={this.state.endDate}
                    onChange={this.handleChangeStart}
                />
                To: 
                <DatePicker
                    dateFormat="DD/MM/YYYY"
                    selected={this.state.endDate}
                    selectsEnd
                    startDate={this.state.startDate}
                    endDate={this.state.endDate}
                    onChange={this.handleChangeEnd}
                />
                <Bootstrap.Button onClick={this.btnClick}>Update logs</Bootstrap.Button>
	   </div>
        );
    }
});

var FilterBtns = React.createClass({
    getInitialState: function () {
        return {
            severities: ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"],
            btnStatus: Array.apply(null, Array(8)).map(function(){return true})
        }
    },

	btnClick: function (key) {
        var btnStatus = this.state.btnStatus.slice(0);
        btnStatus[key] = !btnStatus[key];
        this.setState({btnStatus: btnStatus});
        var checked = [], s = this.state.severities;
        for(var i=0; i<btnStatus.length; i++){
            if(btnStatus[i]) checked.push(s[i]);
        };
        this.props.changeTable(checked);
	},

    render: function () {
        var btnStyle = {
			display: 'inline',
			marginRight: '10px',
            backgroundColor: '#fff'
		};
        var btnStatus = this.state.btnStatus, me = this;
		var btns = this.state.severities.map(function(val, key){
            var style = Object.assign({}, btnStyle);
            if(btnStatus[key]) style['backgroundColor'] = '#eee';
			return <Bootstrap.Button key={key} onClick={me.btnClick.bind(me, key)} style={style}>{val}</Bootstrap.Button>;
		});
		return (
			<div id="log-btns">{btns}</div>
		);
    }
});

var Table = React.createClass({
    getInitialState: function () {
        return {
            selected_log: {}
        }
    },

    rowSelected: function(evt) {
        var selected_row = this.props.logs.find(function(log){
            return log.timestamp === evt.currentTarget.id;
        });
        var selected_row = Object.assign({}, selected_row);
        var msg = JSON.parse(selected_row['message']);
        selected_row['message'] = msg;
        selected_row['message']['method'] = msg['data']['method'];
        delete selected_row['message']['data'];
        this.setState({selected_log: selected_row});
    },

    render: function () {
        var logs = this.props.logs.map(function(log) {
            var msg = JSON.parse(log.message), className = "";
            if(this.state.selected_log.timestamp === log.timestamp)
                className = "info";
            return (
                <Reactable.Tr key={log.timestamp} id={log.timestamp} className={className} onClick={this.rowSelected}>
                    <Reactable.Td column="Timestamp">{log.timestamp.substring(0,19)}</Reactable.Td>
                    <Reactable.Td column="Message">{msg.function}</Reactable.Td>
                    <Reactable.Td column="Severity">{log.severity}</Reactable.Td>
                    <Reactable.Td column="Host">{log.host}</Reactable.Td>
                    <Reactable.Td column="Facility">{log.facility}</Reactable.Td>
                </Reactable.Tr>
            );
        }.bind(this));
        var selected_log = [];
        if("message" in this.state.selected_log){
            var msg = this.state.selected_log.message;
            //msg['method'] = JSON.parse(msg['data'])[;
            for(var key in msg){
                var div = (<div key={key}><b>{key}:</b> {msg[key].toString()}</div>);
                selected_log.push(div);
            }
        }
        var columns = ["Timestamp", "Message", "Severity", "Host", "Facility"];
        return ( <div>
            <Reactable.Table className="table striped tbl-select" columns={columns} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={columns} filterBy={this.props.filterBy} hideFilterInput>
                {logs}
            </Reactable.Table>
            <div className="selected-block">
                {selected_log}
            </div>
        </div> );
    }
});


Log = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Log);

module.exports = Log;
