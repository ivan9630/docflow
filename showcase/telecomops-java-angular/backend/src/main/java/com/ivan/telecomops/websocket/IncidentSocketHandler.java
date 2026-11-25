package com.ivan.telecomops.websocket;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ivan.telecomops.domain.Incident;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
@Component
public class IncidentSocketHandler extends TextWebSocketHandler {
    private final Set<WebSocketSession> sessions=ConcurrentHashMap.newKeySet();
    private final ObjectMapper mapper;
    public IncidentSocketHandler(ObjectMapper mapper){this.mapper=mapper;}
    @Override public void afterConnectionEstablished(WebSocketSession session){sessions.add(session);}
    @Override public void afterConnectionClosed(WebSocketSession session,CloseStatus status){sessions.remove(session);}
    public void broadcast(Incident incident){
        try {
            TextMessage message=new TextMessage(mapper.writeValueAsString(incident));
            for(WebSocketSession s:sessions){
                if(s.isOpen()){
                    try{s.sendMessage(message);}catch(Exception ignored){sessions.remove(s);}
                }
            }
        }catch(Exception e){throw new IllegalStateException("Unable to serialize incident",e);}
    }
}
