for i, face_cropped in enumerate(crops):
                box = boxes_face[i]
                
                # --- LOGIQUE DE TRACKING ET CACHE ---
                matched_face = None
                
                # On cherche si on connaît déjà ce visage (s'il était là à la frame précédente)
                for t_face in tracked_faces:
                    if calculate_center_distance(box, t_face["box"]) < DISTANCE_THRESHOLD:
                        matched_face = t_face
                        break
                
                # Si on l'a reconnu récemment (moins de X secondes)
                if matched_face and (current_time - matched_face["last_pred_time"]) < RECOGNITION_INTERVAL:
                    # On utilise le CACHE, on ne fait AUCUN calcul lourd !
                    name = matched_face["name"]
                    score = matched_face["score"]
                    last_pred_time = matched_face["last_pred_time"]
                
                # Si c'est un nouveau visage OU que le délai X est dépassé
                else:
                    # On lance la PRÉDICTION lourde (Embedding + Qdrant)
                    embedding = await loop.run_in_executor(None, get_embedding, face_cropped)
                    name, score = await loop.run_in_executor(None, search_embedding, embedding)
                    last_pred_time = current_time # On met à jour le chronomètre
                
                # On enregistre l'état actuel pour la prochaine frame
                current_tracked_faces.append({
                    "box": box,
                    "name": name,
                    "score": score,
                    "last_pred_time": last_pred_time
                })

                score_str = f"{score:.2f}" if score else "?"
                names.append(f"{name} ({score_str})")

        # Mise à jour de la mémoire pour la frame suivante
        tracked_faces = current_tracked_faces