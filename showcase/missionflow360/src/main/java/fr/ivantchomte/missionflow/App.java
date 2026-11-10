package fr.ivantchomte.missionflow;
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
public class App {
 private static final Map<Long,Workflow.Item> DATA=new ConcurrentHashMap<>();
 private static final AtomicLong SEQ=new AtomicLong(10);
 static{
  DATA.put(1L,new Workflow.Item(1,"Cadrer un assistant documentaire","IA",Workflow.Priority.HIGH,Workflow.Status.REVIEW,"Produit",16,LocalDate.now()));
  DATA.put(2L,new Workflow.Item(2,"API REST de consolidation métier","JAVA",Workflow.Priority.HIGH,Workflow.Status.IN_PROGRESS,"Développement",24,LocalDate.now()));
  DATA.put(3L,new Workflow.Item(3,"Tableau de bord de qualité des données","DATA",Workflow.Priority.MEDIUM,Workflow.Status.BACKLOG,"Data",12,LocalDate.now()));
  DATA.put(4L,new Workflow.Item(4,"Tests de pipeline CI/CD","DEVOPS",Workflow.Priority.MEDIUM,Workflow.Status.DONE,"Ops",9,LocalDate.now()));
 }
 public static void main(String[] args)throws Exception{
  int port=Integer.parseInt(System.getenv().getOrDefault("PORT","8080"));
  HttpServer s=HttpServer.create(new InetSocketAddress("127.0.0.1",port),0);
  s.createContext("/",App::serve);s.setExecutor(Executors.newVirtualThreadPerTaskExecutor());s.start();
  System.out.println("http://localhost:"+port);
 }
 private static void serve(HttpExchange ex)throws IOException {
  try{
   String path=ex.getRequestURI().getPath(),method=ex.getRequestMethod();
   if(method.equals("GET")&&path.equals("/api/health")){send(ex,200,"{\"status\":\"ok\"}");return;}
   if(method.equals("GET")&&path.equals("/api/items")){send(ex,200,items());return;}
   if(method.equals("GET")&&path.equals("/api/metrics")){send(ex,200,metrics());return;}
   if(method.equals("GET")&&path.startsWith("/api/assist/")){String cat=path.substring(12);send(ex,200,"{\"criteria\":"+strings(Workflow.acceptanceIdeas(cat))+"}");return;}
   if(method.equals("POST")&&path.equals("/api/items")){Map<String,String> f=fields(ex);
    int hours=Integer.parseInt(f.getOrDefault("estimateHours","0"));
    String cat=f.getOrDefault("category","PRODUCT"),title=Workflow.validate(f.get("title"),cat,f.getOrDefault("owner",""),hours);
    Workflow.Priority p=Workflow.Priority.valueOf(f.getOrDefault("priority","MEDIUM"));
    long id=SEQ.incrementAndGet();var item=new Workflow.Item(id,title,cat,p,Workflow.Status.BACKLOG,f.getOrDefault("owner",""),hours,LocalDate.now());
    DATA.put(id,item);send(ex,201,item(item));return;
   }
   if(method.equals("POST")&&path.matches("/api/items/[0-9]+/transition")){
    long id=Long.parseLong(path.split("/")[3]);var old=DATA.get(id);if(old==null){send(ex,404,"{\"error\":\"Introuvable\"}");return;}
    var status=Workflow.Status.valueOf(fields(ex).getOrDefault("status",""));Workflow.assertTransition(old.status(),status);
    var updated=new Workflow.Item(old.id(),old.title(),old.category(),old.priority(),status,old.owner(),old.estimateHours(),old.createdAt());
    DATA.put(id,updated);send(ex,200,item(updated));return;
   }
   if(method.equals("GET")&&path.equals("/api/export.csv")){
    StringBuilder csv=new StringBuilder("id;title;category;priority;status;owner;estimateHours\n");
    for(var t:DATA.values())csv.append(t.id()).append(";").append(t.title().replace(';',',')).append(";").append(t.category()).append(";").append(t.priority()).append(";").append(t.status()).append(";").append(t.owner()).append(";").append(t.estimateHours()).append("\n");
    reply(ex,200,csv.toString().getBytes(StandardCharsets.UTF_8),"text/csv; charset=utf-8");return;
   }
   if(method.equals("GET")&&(path.equals("/")||path.equals("/index.html"))){file(ex,"index.html","text/html; charset=utf-8");return;}
   if(method.equals("GET")&&path.equals("/app.js")){file(ex,"app.js","text/javascript; charset=utf-8");return;}
   if(method.equals("GET")&&path.equals("/styles.css")){file(ex,"styles.css","text/css; charset=utf-8");return;}
   send(ex,404,"{\"error\":\"Route inconnue\"}");
  }catch(IllegalArgumentException e){send(ex,400,"{\"error\":"+q(e.getMessage())+"}");}
   catch(Exception e){send(ex,500,"{\"error\":\"Erreur interne\"}");}
 }
 private static void file(HttpExchange ex,String name,String type)throws IOException{
  var p=Path.of("web",name);if(!Files.exists(p)){send(ex,404,"{\"error\":\"Fichier absent\"}");return;}
  reply(ex,200,Files.readAllBytes(p),type);
 }
 private static Map<String,String> fields(HttpExchange ex)throws IOException{
  Map<String,String> out=new HashMap<>();String form=new String(ex.getRequestBody().readNBytes(8193),StandardCharsets.UTF_8);
  if(form.length()>8192)throw new IllegalArgumentException("Formulaire trop long");
  for(String part:form.split("&")){String[] kv=part.split("=",2);
   if(kv.length>0&&!kv[0].isBlank())out.put(URLDecoder.decode(kv[0],StandardCharsets.UTF_8),URLDecoder.decode(kv.length>1?kv[1]:"",StandardCharsets.UTF_8));
  }return out;
 }
 private static String items(){return DATA.values().stream().sorted(Comparator.comparingLong(Workflow.Item::id)).map(App::item).collect(java.util.stream.Collectors.joining(",","[","]"));}
 private static String item(Workflow.Item i){return "{\"id\":"+i.id()+",\"title\":"+q(i.title())+",\"category\":"+q(i.category())+",\"priority\":"+q(i.priority().name())+",\"status\":"+q(i.status().name())+",\"owner\":"+q(i.owner())+",\"estimateHours\":"+i.estimateHours()+"}";}
 private static String metrics(){var m=Workflow.metrics(DATA.values());return "{\"total\":"+m.get("total")+",\"done\":"+m.get("done")+",\"completionPct\":"+m.get("completionPct")+",\"remainingHours\":"+m.get("remainingHours")+"}";}
 private static String strings(List<String> items){return items.stream().map(App::q).collect(java.util.stream.Collectors.joining(",","[","]"));}
 private static String q(String v){StringBuilder out=new StringBuilder("\"");for(char c:v.toCharArray()){switch(c){case '\\':out.append("\\\\");break;case '"':out.append("\\\"");break;case '\n':out.append("\\n");break;default:if(c<32)out.append(String.format("\\u%04x",(int)c));else out.append(c);}}return out.append('"').toString();}
 private static void send(HttpExchange ex,int code,String value)throws IOException{reply(ex,code,value.getBytes(StandardCharsets.UTF_8),"application/json; charset=utf-8");}
 private static void reply(HttpExchange ex,int code,byte[] bytes,String type)throws IOException{
  ex.getResponseHeaders().set("Content-Type",type);ex.sendResponseHeaders(code,bytes.length);
  try(OutputStream os=ex.getResponseBody()){os.write(bytes);}
 }
}
