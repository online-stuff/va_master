var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var components = require('./basic_components');
var Reactable = require('reactable');
var Router = require('react-router');
var LineChart = require("react-chartjs-2").Line;
var defaults = require("react-chartjs-2").defaults;

var Div = React.createClass({

    render: function () {
        var redux = {};
        var elements = this.props.elements.map(function(element) {
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
        var classes = this.props.class;
        if(typeof this.props.div !== 'undefined'){
            //TODO add other classes
            classes = this.props.div.show;
        }
        return (
            <div className={classes}>
                {elements}
            </div>
        );
    }
});

var MultiTable = React.createClass({

    render: function () {
        var redux = {}, tables = [];
        for(x in this.props.table){
            if(x !== "path"){
                var elements = this.props.elements.map(function(element) {
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
                }.bind(this));
                tables.push(elements);
            }
        }
        return (
            <div className="multi">
                {tables}
            </div>
        );
    }
});

var Chart = React.createClass({
    getInitialState: function () {
        defaults.global.legend.display = true;
        defaults.global.legend.position = 'right';
        var chartData = this.getData(this.props.data, false);
        return {chartOptions: {
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
    },
    getData: function(data, check) {
        var datasets = [], times = [], chartData = {}, prevColors = {};
        if(check){
            for(var i=0; i < this.state.chartData.datasets.length; i++) {
                dataset = this.state.chartData.datasets[i];
                prevColors[dataset.label] = dataset.backgroundColor;
            }
        }
        for(var key in data){
            var obj = {}, prevColor = prevColors[key];
            var color = prevColor || this.getRandomColor();
            obj.label = key;
            obj.data = [];
            var chart_data = data[key];
            for(var i=0; i<chart_data.length; i++){
                obj.data.push(chart_data[i].y);
            }
            obj.backgroundColor = color;
            obj.borderColor = color;
            datasets.push(obj);
        }
        for(var i=0; i<data[key].length; i++){
            times.push(data[key][i].x * 1000);
        }
        chartData.labels = times;
        chartData.datasets = datasets;
        return chartData;
    },
    getRandomColor: function() {
        var letters = '0123456789ABCDEF'.split('');
        var color = '#';
        for (var i = 0; i < 6; i++ ) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    },
    btn_click: function(period, interval, unit, step) {
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
    },
    render: function () {
        return (
            <div>
                <div className="panel_chart">
                    <LineChart name="chart" height={200} data={this.state.chartData} options={this.state.chartOptions} redraw />
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
});

var Table = React.createClass({
    btn_clicked: function(id, evtKey){
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
            var me = this;
            if(typeof evtKey === 'object' && evtKey.type === "download"){
                data.action = evtKey.name;
                data['url_function'] = 'get_backuppc_url';
                Network.download_file('/api/panels/serve_file_from_url', this.props.auth.token, data).done(function(d) {
                    var data = new Blob([d], {type: 'octet/stream'});
                    var url = window.URL.createObjectURL(data);
                    tempLink = document.createElement('a');
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
            var newId = newId.replace(/\s/g, "_");
            Router.hashHistory.push('/chart_panel/' + this.props.panel.server + '/' + newName + '/' + newId);
        }else if('modals' in this.props && evtKey in this.props.modals){
            if("readonly" in this.props){
                var rows = this.props.table[this.props.name].filter(function(row) {
                    if(row[this.props.id] == id[0]){
                        return true;
                    }
                    return false;
                }.bind(this));
                var readonly = {};
                for(key in this.props.readonly){
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
            Router.hashHistory.push('/subpanel/' + this.props.panels[evtKey] + '/' + this.props.panel.server + '/' + id[0]);
        }else{
            var data = {"server_name": this.props.panel.server, "action": evtKey, "args": id};
            var me = this;
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
    },
    linkClicked: function(action, event){
        var linkVal = event.currentTarget.textContent, args = "";
        if(window.location.hash.indexOf('subpanel') > -1){
            args = this.props.panel.args + ","; 
        }
        args += linkVal;
        if("panels" in this.props && action in this.props.panels){
            Router.hashHistory.push('/panel/' + this.props.panels[action] + '/' + this.props.panel.server + '/' + args);
        }else if("subpanels" in this.props && action in this.props.subpanels){
            Router.hashHistory.push('/subpanel/' + this.props.subpanels[action] + '/' + this.props.panel.server + '/' + args);
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
    },
    render: function () {
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
                <Reactable.Th key={tmp.key} column={tmp.key} style={style}>{tmp.label}</Reactable.Th>
            );
        }
        if(!tbl_id){
            tbl_id = this.props.name;
        }
        var action_col = false, action_length = 0;
        if(this.props.hasOwnProperty('actions')){
            var action_col = true, action_length = this.props.actions.length;
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
        var rows = this.props.table[this.props.name].map(function(row) {
            var columns, key, me = this;
            if(typeof row === "string"){
                key = [this.props.name, row];
                columns = (
                    <Reactable.Td key={cols[0]} column={cols[0]}>
                        {row}
                    </Reactable.Td>
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
                columns = this.props.columns.map(function(col, index) {
                    var key = col.key, colClass = "", colText = colVal = row[key];
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
                                colText = <span className={colClass} onClick={me.linkClicked.bind(me, col_arr[1])}>{colVal}</span>
                        }
                    }
                    return (
                        <Reactable.Td key={key} column={key} value={colVal}>
                            {colText}
                        </Reactable.Td>
                    );
                });
            }
            if(action_col){
                action_col = (
                    <Reactable.Td column="action">
                        {action_length > 1 ? (
                            <Bootstrap.DropdownButton id={"dropdown-" + key[0]} bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(this, key)}>
                                {actions}
                            </Bootstrap.DropdownButton>
                        ) : (
                            <Bootstrap.Button bsStyle='primary' onClick={this.btn_clicked.bind(this, key, this.props.actions[0].action)}>
                                {this.props.actions[0].name}
                            </Bootstrap.Button>
                        )}
                    </Reactable.Td>
                );
            }
            var rowClass = "";
            if(typeof this.props.rowStyleCol !== 'undefined'){
                rowClass = "row-" + this.props.rowStyleCol + "-" + row[this.props.rowStyleCol];
            }
            return (
                <Reactable.Tr className={rowClass} key={key}>
                    {columns}
                    {action_col}
                </Reactable.Tr>
            )
        }.bind(this));
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
            { pagination ? ( <Reactable.Table className={className} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={cols} >
                <Reactable.Thead>
                    {tbl_cols}
                </Reactable.Thead>
                {rows}
            </Reactable.Table> ) :
            ( <Reactable.Table className={className} filterable={cols} filterBy={filterBy} noDataText="No matching records found." sortable={true} hideFilterInput >
                <Reactable.Thead>
                    {tbl_cols}
                </Reactable.Thead>
                {rows}
            </Reactable.Table> )}
            </div>
        );
    }
});

//TODO multiple group of checkboxes
var Modal = React.createClass({

    getInitialState: function () {
        var content = this.props.modal.template.content, data = [], checks = {};
        for(j=0; j<content.length; j++){
            if(content[j].type == "Form"){
                var elem = content[j].elements;
                for(i=0; i<elem.length; i++){
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
        return {
            data: data,
            focus: "",
            args: args,
            checks: checks
        };
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },

    action: function(action_name) {
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
        var me = this;
        Network.post("/api/panels/action", this.props.auth.token, data).done(function(d) {
            me.props.dispatch({type: 'CLOSE_MODAL'});
            if('refresh_action' in me.props.modal.template){
                var args = [];
                if(me.props.panel.args !== "") args = [me.props.panel.args];
                var data = {"server_name": me.props.panel.server, "action": me.props.modal.template.refresh_action, "args": args};
                Network.post('/api/panels/action', me.props.auth.token, data).done(function(msg) {
                    if(typeof msg !== 'string'){
                        me.props.dispatch({type: 'CHANGE_DATA', data: msg, name: me.props.modal.template.table_name});
                    }else{
                        me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                    }
                });
            }
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    form_changed: function(e) {
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
    },

    render: function () {
        var btns = this.props.modal.template.buttons.map(function(btn){
            if(btn.action == "cancel"){
                action = this.close;
            }else{
                action = this.action.bind(this, btn.action);
            }
            return <Bootstrap.Button key={btn.name} onClick={action} bsStyle = {btn.class}>{btn.name}</Bootstrap.Button>;
        }.bind(this));

        var redux = {};
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
});

var Path = React.createClass({
    onClick: function(evt){
        // console.log(evt.currentTarget.id)
        // console.log(evt.currentTarget.textContent);
        if(evt.currentTarget.id == 0) return;
        var args = this.props.table.path.slice(0, parseInt(evt.currentTarget.id) + 1);
        var data = {"server_name": this.props.panel.server, "action": this.props.action, "args": args};
        var me = this;
        Network.post('/api/panels/action', this.props.auth.token, data).done(function(msg) {
            if(typeof msg === 'string'){
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            }else{
                me.props.dispatch({type: 'CHANGE_DATA', data: msg, name: me.props.target, initVal: args});
            }
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    render: function () {
        var me = this, paths = [];
        if("path" in this.props.table){
            //TODO remove link from first element in path
            //paths[0] = <li key="0" className="breadcrumb-item">{path}</li>;
            //var p = this.props.table.path.slice(1);
            paths =  this.props.table.path.map(function(path, i){
                return <li key={i} className="breadcrumb-item"><span id={i} className="link" onClick={me.onClick}>{path}</span></li>;
            });
        }
        return (
            <ol className="breadcrumb">
                {paths}
            </ol>
        );
    }
});

var Form = React.createClass({

    onSelect: function (action) {
        var dropdown = ReactDOM.findDOMNode(this.refs.dropdown);
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
    },

    componentDidMount: function(){
        if("focus" in this.props && this.props.focus){
            var elem = this.refs[this.props.focus], pos = elem.value.length;
            elem.focus();
            elem.setSelectionRange(pos, pos);
        }
    },

    render: function () {
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
                    var action = "", defaultValue = "", values = [];
                    if('modal' in this.props){
                        return (<select id={index} key={element.name} name={element.name} defaultValue={this.props.data[index]} onChange={this.props.form_changed} ref={element.name}>
                                    {values.map(function(option, i) {
                                        return <option key={i} value={option}>{option}</option>
                                    })}
                                </select>);
                    }
                    else if('form' in this.props && element.name in this.props.form.dropdowns){
                        d_elem = this.props.form.dropdowns[element.name];
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
                            val = this.props.args[key]
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
});

components.Div = Div;
components.MultiTable = MultiTable;
components.Chart = Chart;
components.Table = Table;
components.Form = Form;
components.Modal = Modal;
components.Path = Path;

module.exports = components;
