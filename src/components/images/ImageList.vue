.file-item {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.class-info {
  margin-top: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 클래스와 퍼센트 정보가 좁은 공간에서도 잘 보이도록 조정 */
.class-info span {
  display: inline-block;
  margin-right: 10px;
} 