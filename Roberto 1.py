import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
if "askAI" in s:
    print("Ya tiene el cerebro de IA, no hago nada."); sys.exit()
old = "rgSay('Te entendí «' + raw + '», pero eso todavía no lo tengo programado, compa. Dime: hora, fecha, linterna, música, Google, llamar o qué comer.');\n        }"
if s.count(old) != 1:
    print("No encontré el lugar para el parche."); sys.exit(1)
new = """askAI(raw);
        }
        var RG_SERVER = 'http://127.0.0.1:8787/';
        var RG_TOKEN = '';
        function askAI(raw){
          var thinking = addMsg('rg', 'Pensando…');
          fetch(RG_SERVER, {method:'POST', headers:{'Content-Type':'application/json','X-RG-Token':RG_TOKEN}, body:JSON.stringify({mensaje:raw})})
            .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
            .then(function(d){ thinking.remove(); rgSay(d.respuesta || 'Me quedé en blanco, compa.'); })
            .catch(function(){ thinking.remove(); rgSay('No pude conectar con mi cerebro ahorita, compa. Checa que el servidor esté prendido.'); });
        }"""
open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("Listo: RG.html ya tiene el cerebro de IA.")
