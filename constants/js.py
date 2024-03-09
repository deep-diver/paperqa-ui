UPDATE_SEARCH_RESULTS = f"""
function search(searchIn, maxResults = 3) {{
    if (searchIn.trim().length > 0) {{
        const results = [];
        let titles = %s;
        for (const title of titles) {{ // Assuming 'titles' is an array defined elsewhere
            if (results.length > 10) {{
                break;
            }} else {{
                if (title.toLowerCase().includes(searchIn.toLowerCase())) {{ // JavaScript's equivalent to Python's 'in'
                    results.push(title);
                }}
            }}
        }}
        // Handle UI elements (Explanation below)
        const resultElements = [1,2,3,4,5,6,7,8,9,10].map(index => {{
            return results[index - 1] || '';
        }});
        if (resultElements[0] == '') {{
            document.getElementById('search_r1').style.display = 'none';
        }} else {{
            document.getElementById('search_r1').style.display = 'block';
        }}
        if (resultElements[1] == '') {{
            document.getElementById('search_r2').style.display = 'none';
        }} else {{
            document.getElementById('search_r2').style.display = 'block';
        }}
        if (resultElements[2] == '') {{
            document.getElementById('search_r3').style.display = 'none';
        }} else {{
            document.getElementById('search_r3').style.display = 'block';
        }}
        if (resultElements[3] == '') {{
            document.getElementById('search_r4').style.display = 'none';
        }} else {{
            document.getElementById('search_r4').style.display = 'block';
        }}
        if (resultElements[4] == '') {{
            document.getElementById('search_r5').style.display = 'none';
        }} else {{
            document.getElementById('search_r5').style.display = 'block';
        }}
        if (resultElements[5] == '') {{
            document.getElementById('search_r6').style.display = 'none';
        }} else {{
            document.getElementById('search_r6').style.display = 'block';
        }}
        if (resultElements[6] == '') {{
            document.getElementById('search_r7').style.display = 'none';
        }} else {{
            document.getElementById('search_r7').style.display = 'block';
        }}
        if (resultElements[7] == '') {{
            document.getElementById('search_r8').style.display = 'none';
        }} else {{
            document.getElementById('search_r8').style.display = 'block';
        }}
        if (resultElements[8] == '') {{
            document.getElementById('search_r9').style.display = 'none';
        }} else {{
            document.getElementById('search_r9').style.display = 'block';
        }}
        if (resultElements[9] == '') {{
            document.getElementById('search_r10').style.display = 'none';
        }} else {{
            document.getElementById('search_r10').style.display = 'block';
        }}
        return resultElements; 
    }} else {{
        document.getElementById('search_r1').style.display = 'none';
        document.getElementById('search_r2').style.display = 'none';
        document.getElementById('search_r3').style.display = 'none';
        document.getElementById('search_r4').style.display = 'none';
        document.getElementById('search_r5').style.display = 'none';
        document.getElementById('search_r6').style.display = 'none';
        document.getElementById('search_r7').style.display = 'none';
        document.getElementById('search_r8').style.display = 'none';
        document.getElementById('search_r9').style.display = 'none';
        document.getElementById('search_r10').style.display = 'none';
        return ['', '', '', '', '', '', '', '', '', '']
    }}
}}
"""

UPDATE_IF_TYPE = """
function chage_if_type() {
    document.querySelector("#chatbot-back").style.display = 'block';
    document.getElementById('qna_block').style.display = 'none';
}
"""


#   globalThis.setStorage = (key, value)=>{
#     localStorage.setItem(key, JSON.stringify(value));
#   }
#   globalThis.getStorage = (key, value)=>{
#     return JSON.parse(localStorage.getItem(key));
#   }

OPEN_CHAT_IF = """
function (arXivId) { 
    var localData = localStorage.getItem('localData');
    if (!localData) {
      localData = {}; // Initialize if it doesn't exist
    }
    else {
      localData = JSON.parse(localData);
    } 

    if (!localData[arXivId]) {
      localData[arXivId] = { ctx: '', pingpongs: [] };
    }

    localStorage.setItem('localData', JSON.stringify(localData));

    document.querySelector("#chatbot-back").classList.add("visible");

    pingpongs = [];
    localData[arXivId]['pingpongs'].forEach(element =>{  
      pingpongs.push([element.ping, element.pong]);
    });

    return [localData[arXivId], pingpongs];
}
"""

CLOSE_CHAT_IF = """
function close() {
    setTimeout(function() {
    document.querySelector("#chatbot-back").classList.remove("visible"); // Remove after a slight delay
    }, 100); // 100-millisecond delay
}
"""

UPDATE_CHAT_HISTORY = """
function (arXivId, data) { 
    console.log(arXivId)
    console.log(data);
    if (localStorage.getItem('localData') === null) {
        localStorage['localData'] = {}; 
    }

    var localData = localStorage.getItem('localData');
    localData = JSON.parse(localData);
    localData[arXivId] = data;
    console.log(localData[arXivId]);
    localStorage.setItem('localData', JSON.stringify(localData));
}
"""


GET_LOCAL_STORAGE = """
function() {
  globalThis.setStorage = (arXivId, value) => {
    console.log(value);
    if (localStorage.getItem('localData') === null) {
        localStorage['localData'] = {}; 
    }

    var localData = localStorage.getItem('localData');
    localData = JSON.parse(localData);
    localData[arXivId] = value;
    console.log(localData[arXivId]);
    localStorage.setItem('localData', JSON.stringify(localData));
  }

  globalThis.getStorage = (arXivId)=>{
    var localData = localStorage.getItem('localData');
    console.log(localData);
    if (!localData) {
      localData = {}; // Initialize if it doesn't exist
    }
    else {
      localData = JSON.parse(localData);
    } 

    if (!localData[arXivId]) {
      localData[arXivId] = { ctx: '', pingpongs: [] };
    }

    localStorage.setItem('localData', JSON.stringify(localData));
    console.log(localData[arXivId]['pingpongs']);
    return [localData[arXivId], localData[arXivId]['pingpongs']];
  } 

  var localData = localStorage.getItem('localData');

  if(!localData) {
    localData = {}
    localStorage.setItem('localData', JSON.stringify(localData));
  }
  return [localData['%s']['pingpongs'], localData];
}
"""