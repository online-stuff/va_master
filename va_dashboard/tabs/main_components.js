import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import { connect } from 'react-redux';
var Network = require('../network');
import { findDOMNode } from 'react-dom';
var components = require('./basic_components');
import { Table as Reactable, Tr, Th, Thead, Td } from 'reactable';
import { hashHistory } from 'react-router';
import { Line, Pie, Bar, defaults } from "react-chartjs-2";
var moment = require('moment');
import { DateRangePicker } from 'react-dates';
import { getRandomColor } from './util';

const Div = (props) => {
    var redux = {};
    var elements = props.elements.map(function(element) {
        element.key = element.name;
        var Component = components[element.type];
        redux[element.type] = connect(function(state){
            var newstate = {auth: state.auth};
            if(typeof element.reducers !== 'undefined'){
                var r = element.reducers;
                for (var i = 0; i < r.length; i++) {
                    newstate[r[i]] = state[r[i]];
                }
            }
            return newstate;
        })(Component);
        var Redux = redux[element.type];
        return React.createElement(Redux, element);
    });
    var classes = props.class;
    if(typeof props.div !== 'undefined'){
        //TODO add other classes
        classes = props.div.show;
    }
    return (
        <div className={classes}>
            {elements}
        </div>
    );
}

const MultiTable = (props) => {
    var redux = {}, tables = [];
    for(var x in props.table){
        if(x !== "path"){
            var elements = props.elements.map((element) => {
                element.name = x;
                element.key = element.type + element.name;
                var Component = components[element.type];
                redux[element.type] = connect(function(state){
                    var newstate = {auth: state.auth};
                    if(typeof element.reducers !== 'undefined'){
                        var r = element.reducers;
                        for (var i = 0; i < r.length; i++) {
                            newstate[r[i]] = state[r[i]];
                        }
                    }
                    return newstate;
                })(Component);
                var Redux = redux[element.type];
                return React.createElement(Redux, element);
            });
            tables.push(elements);
        }
    }
    return (
        <div className="multi">
            {tables}
        </div>
    );
}

class Chart extends Component {
    constructor (props) {
        super(props);
        defaults.global.legend.display = true;
        defaults.global.legend.position = 'right';
        var chartData = this.getData(this.props.data, false);
        this.state = {chartOptions: {
            maintainAspectRatio: false,
            responsive: true,
            scales: {
                xAxes: [{
                    type: 'time',
                    stacked: true,
                    time: {
                        displayFormats: {
                            minute: 'HH:mm',
                            hour: 'HH:mm',
                            second: 'HH:mm:ss',
                        },
                        tooltipFormat: 'DD/MM/YYYY HH:mm',
                        unit: 'minute',
                        unitStepSize: 5
                    }
                }],
                yAxes: [{
                    stacked: true
                }]
            }
        }, chartData: chartData};
        this.getData = this.getData.bind(this);
        this.btn_click = this.btn_click.bind(this);
    }
    getData(data, check) {
        var datasets = [], times = [], chartData = {}, prevColors = {};
        if(check){
            for(let i=0; i < this.state.chartData.datasets.length; i++) {
                let dataset = this.state.chartData.datasets[i];
                prevColors[dataset.label] = dataset.backgroundColor;
            }
        }
        for(var key in data){
            var obj = {}, prevColor = prevColors[key];
            var color = prevColor || getRandomColor();
            obj.label = key;
            obj.data = [];
            var chart_data = data[key];
            for(let i=0; i<chart_data.length; i++){
                obj.data.push(chart_data[i].y);
            }
            obj.backgroundColor = color;
            obj.borderColor = color;
            datasets.push(obj);
        }
        for(let i=0; i<data[key].length; i++){
            times.push(data[key][i].x * 1000);
        }
        chartData.labels = times;
        chartData.datasets = datasets;
        return chartData;
    }
    btn_click (period, interval, unit, step) {
        var server_name = this.props.panel.server;
        var data = {"server_name": server_name, "args": [this.props.provider, this.props.service, period, interval]};
        var me = this;
        Network.post('/api/panels/chart_data', this.props.auth.token, data).done(function(d) {
            var chartOptions = Object.assign({}, me.state.chartOptions);
            chartOptions.scales.xAxes[0].time.unit = unit;
            chartOptions.scales.xAxes[0].time.unitStepSize = step;
            me.setState({chartData: me.getData(d[server_name], true), chartOptions: chartOptions});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
    render () {
        return (
            <div>
                <div className="panel_chart">
                    <Line name="chart" height={200} data={this.state.chartData} options={this.state.chartOptions} redraw />
                </div>
                <div id="chartBtns">
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-1h", "300", 'minute', 5)}>Last hour</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-5h", "1500", 'hour', 1)}>Last 5 hours</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-1d", "7200", 'hour', 4)}>Last day</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-7d", "86400", 'day', 1)}>Last week</button>
                  <button className='btn btn-primary bt-sm chartBtn' onClick = {this.btn_click.bind(this, "-1m", "86400", 'day', 5)}>Last month</button>
                </div>
            </div>
        );
    }
}

class Table extends Component {
    btn_clicked(id, evtKey){
        var checkPath = 'path' in this.props.table && this.props.table.path.length > 0;
        if(!checkPath && 'args' in this.props.panel && this.props.panel.args !== ""){
            id.unshift(this.props.panel.args);
        }
        if(checkPath){
            var args = [this.props.table.path[0]]
            if(this.props.table.path.length > 1){
                args.push(this.props.table.path[1]);
                var rest = this.props.table.path.slice(2,);
                var path = "", slash = rest.length > 0 ? '/' : '';
                for(var i=1; i<rest.length; i++){
                    path += rest[i];
                }
                if(slash)
                    args.push(rest[0]);
                args.push(path + slash + id[0]);
            }else{
                args.push(id[0]);
            }
            var data = {"server_name": this.props.panel.server, "action": evtKey, "args": args};
            let me = this;
            if(typeof evtKey === 'object' && evtKey.type === "download"){
                data.action = evtKey.name;
                data['url_function'] = 'get_backuppc_url';
                Network.download_file('/api/panels/serve_file_from_url', this.props.auth.token, data).done(function(d) {
                    var data = new Blob([d], {type: 'octet/stream'});
                    var url = window.URL.createObjectURL(data);
                    let tempLink = document.createElement('a');
                    tempLink.style = "display: none";
                    tempLink.href = url;
                    tempLink.setAttribute('download', id[0]);
                    document.body.appendChild(tempLink);
                    tempLink.click();
                    setTimeout(function(){
                        document.body.removeChild(tempLink);
                        window.URL.revokeObjectURL(url);
                    }, 100);
                }).fail(function (msg) {
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                });
            }else{
                Network.post('/api/panels/action', this.props.auth.token, data).done(function(msg) {
                    if(typeof msg === 'string'){
                        me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                    }
                }).fail(function (msg) {
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                });
            }
        }else if(evtKey == 'chart'){
            var newName = this.props.name.replace(/\s/g, "_");
            var newId = id[0].replace(/:/g, "_");
            newId = newId.replace(/\s/g, "_");
            hashHistory.push('/chart_panel/' + this.props.panel.server + '/' + newName + '/' + newId);
        }else if('modals' in this.props && evtKey in this.props.modals){
            if("readonly" in this.props){
                var rows = this.props.table[this.props.name].filter(function(row) {
                    if(row[this.props.id] == id[0]){
                        return true;
                    }
                    return false;
                }.bind(this));
                var readonly = {};
                for(let key in this.props.readonly){
                    readonly[this.props.readonly[key]] = rows[0][key];
                }
                this.props.dispatch({type: 'SET_READONLY', readonly: readonly});
            }
            var modal = Object.assign({}, this.props.modals[evtKey]);
            modal.args = id;
            modal.table_name = this.props.name;
            modal.refresh_action = this.props.source;
            this.props.dispatch({type: 'OPEN_MODAL', template: modal});
        }else if("panels" in this.props && evtKey in this.props.panels){
            hashHistory.push('/subpanel/' + this.props.panels[evtKey] + '/' + this.props.panel.server + '/' + id[0]);
        }else{
            var data = {"server_name": this.props.panel.server, "action": evtKey, "args": id};
            let me = this;
            Network.post('/api/panels/action', this.props.auth.token, data).done(function(msg) {
                if(typeof msg === 'string'){
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                }else{
                    data.action = me.props.source;
                    data.args = [];
                    if('args' in me.props.panel && me.props.panel.args !== ""){
                        data.args = [me.props.panel.args];
                    }
                    Network.post('/api/panels/action', me.props.auth.token, data).done(function(msg) {
                        if(typeof msg !== 'string'){
                            me.props.dispatch({type: 'CHANGE_DATA', data: msg, name: me.props.name});
                        }else{
                            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                        }
                    });
                }
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }
    }
    linkClicked(action, event){
        var linkVal = event.currentTarget.textContent, args = "";
        if(window.location.hash.indexOf('subpanel') > -1){
            args = this.props.panel.args + ","; 
        }
        args += linkVal;
        if("panels" in this.props && action in this.props.panels){
            hashHistory.push('/panel/' + this.props.panels[action] + '/' + this.props.panel.server + '/' + args);
        }else if("subpanels" in this.props && action in this.props.subpanels){
            hashHistory.push('/subpanel/' + this.props.subpanels[action] + '/' + this.props.panel.server + '/' + args);
        } else {
             var args = this.props.table.path.concat(linkVal);
             var data = {"server_name": this.props.panel.server, "action": action, "args": args};
             var me = this;
             Network.post('/api/panels/action', this.props.auth.token, data).done(function(msg) {
                 if(typeof msg === 'string'){
                     me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                 }else{
                     me.props.dispatch({type: 'CHANGE_DATA', data: msg, name: me.props.name, passVal: linkVal});
                 }
             }).fail(function (msg) {
                 me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
             });
        }
    }
    render () {
        var pagination = "pagination" in this.props ? this.props.pagination : true;
        if(typeof this.props.table[this.props.name] === 'undefined')
            return null;
        var cols = [], tbl_cols = this.props.columns.slice(0), tbl_id = this.props.id;
        for(var i=0; i<tbl_cols.length; i++){
            var tmp = Object.assign({}, tbl_cols[i]);
            if(tmp.key === ""){
                tmp.key = this.props.name;
                tmp.label = this.props.name;
            }
            // if("action" in tmp){
            //     cols.push(tmp);
            // }else{
            //     cols.push(tmp.key);
            // }
            var style = null;
            if("width" in tmp){
                style = {"width": tmp.width};
            }
            cols.push(tmp.key);
            tbl_cols[i] = (
                <Th key={tmp.key} column={tmp.key} style={style}>{tmp.label}</Th>
            );
        }
        if(!tbl_id){
            tbl_id = this.props.name;
        }
        var action_col = false, action_length = 0;
        if(this.props.hasOwnProperty('actions')){
            action_col = true; 
            action_length = this.props.actions.length;
            if(action_length > 1){
                var actions = this.props.actions.map(function(action) {
                    var className = "";
                    if(typeof action.class !== 'undefined'){
                        className = action.class;
                    }
                    return (
                        <Bootstrap.MenuItem key={action.name} eventKey={action.action} className={className}>{action.name}</Bootstrap.MenuItem>
                    );
                });
            }
        }
        var rows = this.props.table[this.props.name].map((row) => {
            var columns, key;
            if(typeof row === "string"){
                key = [this.props.name, row];
                columns = (
                    <Td key={cols[0]} column={cols[0]}>
                        {row}
                    </Td>
                );
            }else{
                if(tbl_id instanceof Array){
                    key = [];
                    for(var i=0; i<tbl_id.length; i++){
                        key.push(row[tbl_id[i]]);
                    }
                }else{
                    key = [row[tbl_id]];
                }
                columns = this.props.columns.map((col, index) => {
                    var key = col.key, colClass = "", colText = row[key], colVal = row[key];
                    if(typeof col.href !== 'undefined'){
                        colText = <a href={colVal} target='_blank'>Link</a>
                    }
                    else if(typeof col.colClass !== 'undefined'){
                        colClass = col.colClass;
                        if(row[col.colClass]){
                            colClass = "col-" + col.colClass + "-" + row[col.colClass];
                        }
                        colText = <span className={colClass}>{colVal}</span>;
                        if("action" in col){
                            var col_arr = col['action'].split(':');
                            if(col_arr[0] === "all" || col_arr[0] === row[col.colClass])
                                colText = <span className={colClass} onClick={this.linkClicked.bind(this, col_arr[1])}>{colVal}</span>
                        }
                    }
                    return (
                        <Td key={key} column={key} value={colVal}>
                            {colText}
                        </Td>
                    );
                });
            }
            if(action_col){
                action_col = (
                    <Td column="action">
                        {action_length > 1 ? (
                            <Bootstrap.DropdownButton id={"dropdown-" + key[0]} bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(this, key)}>
                                {actions}
                            </Bootstrap.DropdownButton>
                        ) : (
                            <Bootstrap.Button bsStyle='primary' onClick={this.btn_clicked.bind(this, key, this.props.actions[0].action)}>
                                {this.props.actions[0].name}
                            </Bootstrap.Button>
                        )}
                    </Td>
                );
            }
            var rowClass = "";
            if(typeof this.props.rowStyleCol !== 'undefined'){
                rowClass = "row-" + this.props.rowStyleCol + "-" + row[this.props.rowStyleCol];
            }
            return (
                <Tr className={rowClass} key={key}>
                    {columns}
                    {action_col}
                </Tr>
            )
        });
        var filterBy = "";
        if('filter' in this.props){
            filterBy = this.props.filter.filterBy;
        }
        var className = "table striped";
        if('class' in this.props){
            className += " " + this.props.class;
        }
        return (
            <div>
            { pagination ? ( <Reactable className={className} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={cols} >
                <Thead>
                    {tbl_cols}
                </Thead>
                {rows}
            </Reactable> ) :
            ( <Reactable className={className} filterable={cols} filterBy={filterBy} noDataText="No matching records found." sortable={true} hideFilterInput >
                <Thead>
                    {tbl_cols}
                </Thead>
                {rows}
            </Reactable> )}
            </div>
        );
    }
}

//TODO multiple group of checkboxes
class Modal extends Component {

    constructor (props) {
        super(props);
        var content = this.props.modal.template.content, data = [], checks = {};
        for(var j=0; j<content.length; j++){
            if(content[j].type == "Form"){
                var elem = content[j].elements;
                for(let i=0; i<elem.length; i++){
                    if(elem[i].type === 'dropdown')
                        data[i] = elem[i].value[0];
                    if(elem[i].type !== 'label')
                        data[i] = elem[i].value;
                    if(elem[i].type === 'checkbox')
                        checks[i] = elem[i].name;
                }
            }
        }
        var args = [];
        if("args" in this.props.modal.template){
            args = this.props.modal.template.args;
        }
        this.state = {
            data: data,
            focus: "",
            args: args,
            checks: checks
        };
        this.close = this.close.bind(this);
        this.action = this.action.bind(this);
        this.form_changed = this.form_changed.bind(this);
    }

    close () {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    }

    action (action_name) {
        var args = this.state.data.slice(0);
        var checks = this.state.checks, keys = Object.keys(checks);
        if(keys.length > 0){
            var j = 0, index = 0, length = args.length, check_vals = [];
            for(var i=0; i<length; i++){
                if(args[index] === false){
                    args.splice(index, 1);
                    j++; 
                }else if(args[index] === true){
                    args.splice(index, 1);
                    check_vals.push(checks[j++]);
                }
                index = i + 1 - j;
            }
            args.splice(keys[0], 0, check_vals);
        }
        var data = {"server_name": this.props.panel.server, "action": action_name, "args": this.state.args.concat(args)};
        Network.post("/api/panels/action", this.props.auth.token, data).done((d) => {
            this.props.dispatch({type: 'CLOSE_MODAL'});
            if('refresh_action' in this.props.modal.template){
                var args = [];
                if(this.props.panel.args !== "") args = [this.props.panel.args];
                var data = {"server_name": this.props.panel.server, "action": this.props.modal.template.refresh_action, "args": args};
                Network.post('/api/panels/action', this.props.auth.token, data).done(function(msg) {
                    if(typeof msg !== 'string'){
                        this.props.dispatch({type: 'CHANGE_DATA', data: msg, name: this.props.modal.template.table_name});
                    }else{
                        this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                    }
                });
            }
        }).fail(function (msg) {
            this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    form_changed(e) {
        var name = e.target.name;
        var val = e.target.value;
        var id = e.target.id;
        var data = this.state.data;
        if(e.target.type == "checkbox"){
            val = e.target.checked;
        }else{
            this.setState({focus: name});
        }
        data[id] = val;
        this.setState({data: data});
    }

    render () {
        var redux = {}, action;
        var btns = this.props.modal.template.buttons.map((btn) => {
            if(btn.action == "cancel"){
                action = this.close;
            }else{
                action = this.action.bind(this, btn.action);
            }
            return <Bootstrap.Button key={btn.name} onClick={action} bsStyle = {btn.class}>{btn.name}</Bootstrap.Button>;
        });

        var elements = this.props.modal.template.content.map(function(element) {
            element.key = element.name;
            var Component = components[element.type];
            if(element.type == "Form"){
                element.data = this.state.data;
                element.form_changed = this.form_changed;
                element.focus = this.state.focus;
                element.modal = true;
            }
            redux[element.type] = connect(function(state){
                var newstate = {auth: state.auth};
                if(typeof element.reducers !== 'undefined'){
                    var r = element.reducers;
                    for (var i = 0; i < r.length; i++) {
                        newstate[r[i]] = state[r[i]];
                    }
                }
                return newstate;
            })(Component);
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        }.bind(this));
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>{this.props.modal.template.title}</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                {elements}
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
              {btns}
            </Bootstrap.Modal.Footer>

        </Bootstrap.Modal>
        );
    }
}

class Path extends Component {
	onClick(evt) {
		// console.log(evt.currentTarget.id)
		// console.log(evt.currentTarget.textContent);
		if(evt.currentTarget.id == 0) return;
		var args = this.props.table.path.slice(0, parseInt(evt.currentTarget.id) + 1);
		var data = {"server_name": this.props.panel.server, "action": this.props.action, "args": args};
		Network.post('/api/panels/action', this.props.auth.token, data).done((msg) => {
			if(typeof msg === 'string'){
				this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
			}else{
				this.props.dispatch({type: 'CHANGE_DATA', data: msg, name: this.props.target, initVal: args});
			}
		}).fail((msg) => {
			this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
		});
	}
    render () {
        var paths = [];
        if("path" in this.props.table){
            //TODO remove link from first element in path
            //paths[0] = <li key="0" className="breadcrumb-item">{path}</li>;
            //var p = this.props.table.path.slice(1);
            paths =  this.props.table.path.map((path, i) => {
                return <li key={i} className="breadcrumb-item"><span id={i} className="link" onClick={(e) => this.onClick(e)}>{path}</span></li>;
            });
        }
        return (
            <ol className="breadcrumb">
                {paths}
            </ol>
        );
    }
}

class Form extends Component {

    onSelect (action) {
        var dropdown = findDOMNode(this.refs.dropdown);
        var host = dropdown.value.trim();
        var d_name = dropdown.name;
        var data = {"server_name": this.props.panel.server, "action": action, "args": [host]};
        var me = this;
        Network.post('/api/panels/action', this.props.auth.token, data).done(function(msg) {
            if(typeof msg === 'string'){
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            }else if('val' in msg){
                me.props.dispatch({type: 'SELECT', select: host, name: d_name});
                me.props.dispatch({type: 'CHANGE_DATA', data: msg.list, name: me.props.target, initVal: [host, msg.val]});
            }else{
                me.props.dispatch({type: 'SELECT', select: host, name: d_name});
                me.props.dispatch({type: 'CHANGE_DATA', data: msg, name: me.props.target, initVal: [host]});
            }
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    componentDidMount(){
        if("focus" in this.props && this.props.focus){
            var elem = this.refs[this.props.focus], pos = elem.value.length;
            elem.focus();
            elem.setSelectionRange(pos, pos);
        }
    }

    render () {
        var redux = {};

        var inputs = this.props.elements.map(function(element, index) {
            var type = element.type;
            if(type.charAt(0) === type.charAt(0).toLowerCase()){
                if(type == "checkbox"){
                    return ( <Bootstrap.Checkbox id={index} key={element.name} name={element.name} checked={this.props.data[index]} inline onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                if(type == "label"){
                    return ( <label id={index} key={element.name} name={element.name} className="block">{element.value.split('\n').map(function(item, key){
                        return <span key={key}>{item}<br/></span>
                    })}</label>);
                }
                if(type == "multi_checkbox"){
                    return ( <Bootstrap.Checkbox id={index} key={element.name} name={element.name} checked={this.props.data[index]} onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                if(type == "readonly_text"){
                    return ( <input id={index} key={element.name} className="form-control" type={type} name={element.name} value={this.props.form.readonly[element.name]} disabled /> );
                }
                if(type == "dropdown"){
                    var action = "", defaultValue = "", values = element.values;
                    if('modal' in this.props){
                        return (<select id={index} key={element.name} name={element.name} defaultValue={this.props.data[index]} onChange={this.props.form_changed} ref={element.name}>
                                    {values.map(function(option, i) {
                                        return <option key={i} value={option}>{option}</option>
                                    })}
                                </select>);
                    }
                    else if('form' in this.props && element.name in this.props.form.dropdowns){
                        let d_elem = this.props.form.dropdowns[element.name];
                        defaultValue = d_elem.select;
                        values = d_elem.values;
                    }else{
                        defaultValue = element.value[0];
                        values = element.value;
                    }
                    if("action" in element){
                        action = this.onSelect.bind(this, element.action);
                    }
                    return ( <select ref="dropdown" id={index} key={element.name} onChange={action} name={element.name} defaultValue={defaultValue}>
                        {values.map(function(option, i) {
                            return <option key={i} value={option}>{option}</option>
                        })}
                    </select> );
                }
                return ( <input id={index} key={element.name} type={type} name={element.name} className="form-control" value={this.props.data[index]} placeholder={element.label} onChange={this.props.form_changed} ref={element.name} /> );
            }
            element.key = element.name;
            //if(Object.keys(redux).indexOf(type) < 0){
                if(type == "Button" && element.action == "modal"){
                    var modalTemplate = Object.assign({}, element.modal), args = [];
                    if('panel' in this.props && 'args' in this.props.panel && this.props.panel.args){
                        args.push(this.props.panel.args);
                    }
                    if('args' in this.props){
                        for(var key in this.props.args){
                            let val = this.props.args[key]
                            if(!val){
                                val = this.props.name;
                            }
                            args.push(val);
                        }
                    }
                    modalTemplate.args = args;
                    element.modalTemplate = modalTemplate;
                }
                var Component = components[type];
                redux[type] = connect(function(state){
                    var newstate = {auth: state.auth};
                    if(typeof element.reducers !== 'undefined'){
                        var r = element.reducers;
                        for (var i = 0; i < r.length; i++) {
                            newstate[r[i]] = state[r[i]];
                        }
                    }
                    return newstate;
                })(Component);
            //}
            var Redux = redux[type];
            return React.createElement(Redux, element);
        }.bind(this));

        return (
            <form className={this.props.class}>
                {inputs}
            </form>
        );
    }
}

class FilterForm extends Component {
    constructor(props) {
        super(props);
        let inputs = {};
        this.props.columns.map(col => {
            let { name, type } = col
            if(type !== 'dates'){
                inputs[name] = '';
            }
        });
        this.state = {
            ...inputs,
            startDate: moment().subtract(1, 'days'),
            endDate: moment(),
            focusedInput: null
        };
        this.sendFilter = this.sendFilter.bind(this);
    }
    sendFilter(){
        Network.post('/api/panels/action', this.props.auth.token, this.state).done(msg => {
            this.props.dispatch({type: 'CHANGE_DATA', name: this.props.target, data: msg.data});
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg});
        });
    }
    render(){
        let inputs = this.props.columns.map(col => {
            let { name, type } = col, input;
            switch(type){
                case 'dates':
                    input = (
						<DateRangePicker
							displayFormat="DD/MM/YYYY"
							startDate={this.state.startDate}
							endDate={this.state.endDate}
							onDatesChange={({ startDate, endDate }) => this.setState({ startDate, endDate })}
							focusedInput={this.state.focusedInput}
							onFocusChange={focusedInput => this.setState({ focusedInput })}
							isOutsideRange={() => false}
						/>
                    );
                    break;
                default:
                    input = <input type={type} value={this.state[name]} onChange={val => this.setState({name: val})} />;
                    break;
            }
            return (
                <div className="filter-form-input">
                    <label>{name}</label>
                    {input}
                </div>
            );
        });
        return (
            <div>
                {inputs}
                <button className='btn btn-primary' onClick={this.sendFilter}>Filter</button>
            </div>
        );
    }
}

const chartOptionsTime = {
    maintainAspectRatio: false,
    responsive: true,
    scales: {
        xAxes: [{
            type: 'time',
            stacked: true,
            time: {
                displayFormats: {
                    minute: 'HH:mm',
                    hour: 'HH:mm',
                    second: 'HH:mm:ss',
                },
                tooltipFormat: 'DD/MM/YYYY HH:mm',
                //unit: 'minute',
                //i....unitStepSize: 5
            }
        }],
        yAxes: [{
            stacked: true
        }]
    }
};

const chartOptions = {
	maintainAspectRatio: false,
	responsive: true,
	scales: {
		xAxes: [{
			stacked: true,
		}],
		yAxes: [{
			stacked: true
		}]
	}
};

const chartOptionsPie = {
	maintainAspectRatio: false,
	//cutoutPercentage: 70,
	//rotation: 1 * Math.PI,
	//circumference: 1 * Math.PI
};

class CustomChart extends Component {
    constructor(props) {
        super(props);
        let chartData = {chartData: this.parseData(props)};
        this.state = chartData;
    }
    parseData(props) {
        let { table, target, xCol, xColType, datasets, column } = props, xData = [];
        let data = Object.assign([], datasets), chartData = {};
        if(xCol){
			table[target].map((row) => {
				xData.push(row[xCol]); //new Date(row[xCol])
                data.forEach(elem => {
                    elem.data.push(row[elem.column]);
                });
			});
        }else{
            //data.forEach(elem => {
            //    xData.push(elem.name);
            //});
			/*table[target].map((row) => {
                xData.push(row[xCol]);
                data.forEach(elem => {
                    elem.data.push(row[column]);
                });
			});*/
		}
        chartData.labels = xData;
        chartData.datasets = data;
        return chartData;
    }
    componentWillReceiveProps(nextProps) {
        let chartData = this.parseData(nextProps);
        this.setState({ chartData });
    }
    render() {
        let { name, height, chartType } = this.props, chart;
        switch(chartType) {
            case 'line':
                chart = <Line name={name} height={height || 200} data={this.state.chartData} options={chartOptions} redraw />;
                break;
            case 'pie':
                chart = <Pie data={this.state.chartData} options={chartOptionsPie}/>;
                break;
            case 'bar':
                chart = <Bar data={this.state.chartData} options={chartOptions} redraw />
                break;
        }
        return (
            <div>
                {chart}
            </div>
        );
    }
}

components.Div = Div;
components.MultiTable = MultiTable;
components.Chart = Chart;
components.Table = Table;
components.Form = Form;
components.Modal = Modal;
components.Path = Path;
components.CustomChart = CustomChart;

module.exports = components;
