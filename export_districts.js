const { data } = require('province-city-china/data');
const fs = require('fs');

fs.writeFileSync('districts_data.json', JSON.stringify(data));